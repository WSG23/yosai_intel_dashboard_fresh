#!/usr/bin/env python3
"""
Complete File Upload Page - Missing piece for consolidation
Integrates with analytics system
"""
import logging
import json
from datetime import datetime

import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from dash import html, dcc
from dash.dash import no_update
from dash._callback_context import callback_context
from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from analytics.controllers import UnifiedAnalyticsController
import logging

logger = logging.getLogger(__name__)
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
from services.device_learning_service import (
    DeviceLearningService,
    get_device_learning_service,
)
from services.upload_service import process_uploaded_file, create_file_preview
from utils.upload_store import uploaded_data_store as _uploaded_data_store
from config.dynamic_config import dynamic_config

from components.column_verification import (
    save_verified_mappings,
)
from services.ai_suggestions import generate_column_suggestions


logger = logging.getLogger(__name__)


def analyze_device_name_with_ai(device_name):
    """Return AI-generated device info unless a user mapping exists."""
    try:
        from services.ai_mapping_store import ai_mapping_store

        # Check for user-confirmed mapping first
        mapping = ai_mapping_store.get(device_name)
        if mapping:
            if mapping.get("source") == "user_confirmed":
                logger.info(
                    f"\U0001f512 Using USER CONFIRMED mapping for '{device_name}'"
                )
                return mapping

        # Only use AI if no user mapping exists
        logger.info(
            f"\U0001f916 No user mapping found, generating AI analysis for '{device_name}'"
        )

        from services.ai_device_generator import AIDeviceGenerator

        ai_generator = AIDeviceGenerator()
        result = ai_generator.generate_device_attributes(device_name)

        ai_mapping = {
            "floor_number": result.floor_number,
            "security_level": result.security_level,
            "confidence": result.confidence,
            "is_entry": result.is_entry,
            "is_exit": result.is_exit,
            "device_name": result.device_name,
            "ai_reasoning": result.ai_reasoning,
            "source": "ai_generated",
        }

        return ai_mapping

    except Exception as e:
        logger.info(f"\u274c Error in device analysis: {e}")
        return {
            "floor_number": 1,
            "security_level": 5,
            "confidence": 0.1,
            "source": "fallback",
        }


def build_success_alert(
    filename: str,
    rows: int,
    cols: int,
    prefix: str = "Successfully uploaded",
    processed: bool = True,
) -> dbc.Alert:
    """Create a success alert showing current row and column counts."""

    # CRITICAL: Use actual current data, not cached values
    details = f"📊 {rows:,} rows × {cols} columns"
    if processed:
        details += " processed"

    # Clear timestamp to avoid showing stale data
    from datetime import datetime

    timestamp = datetime.now().strftime("%H:%M:%S")

    return dbc.Alert(
        [
            html.H6(
                [html.I(className="fas fa-check-circle me-2"), f"{prefix} {filename}"],
                className="alert-heading",
            ),
            html.P(
                [
                    details,
                    html.Br(),
                    html.Small(f"Processed at {timestamp}", className="text-muted"),
                ]
            ),
        ],
        color="success",
        className="mb-3",
    )


def build_failure_alert(message: str) -> dbc.Alert:
    """Return a Bootstrap alert describing a failed file upload."""

    return dbc.Alert(
        [html.H6("Upload Failed", className="alert-heading"), html.P(message)],
        color="danger",
    )


def auto_apply_learned_mappings(df: pd.DataFrame, filename: str) -> bool:
    """Auto-apply any learned mappings for this file type"""
    try:
        learning_service = get_device_learning_service()

        learned_mappings = learning_service.get_learned_mappings(df, filename)

        if learned_mappings:
            learning_service.apply_learned_mappings_to_global_store(df, filename)
            logger.info(
                f"🤖 Auto-applied {len(learned_mappings)} learned device mappings"
            )
            return True
        return False

    except Exception as e:
        logger.error(f"Failed to auto-apply learned mappings: {e}")
        return False


def build_file_preview_component(df: pd.DataFrame, filename: str) -> html.Div:
    """Return a preview card and configuration buttons for an uploaded file."""

    return html.Div(
        [
            create_file_preview(df, filename),
            dbc.Card(
                [
                    dbc.CardHeader(
                        [html.H6("📋 Data Configuration", className="mb-0")]
                    ),
                    dbc.CardBody(
                        [
                            html.P(
                                "Configure your data for analysis:", className="mb-3"
                            ),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        "📋 Verify Columns",
                                        id="verify-columns-btn-simple",
                                        color="primary",
                                        size="sm",
                                    ),
                                    dbc.Button(
                                        "🤖 Classify Devices",
                                        id="classify-devices-btn",
                                        color="info",
                                        size="sm",
                                    ),
                                ],
                                className="w-100",
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            ),
        ]
    )


def layout():
    """File upload page layout with persistent storage"""
    return dbc.Container(
        [
            # Page header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1("📁 File Upload", className="text-primary mb-2"),
                            html.P(
                                "Upload CSV, Excel, or JSON files for analysis",
                                className="text-muted mb-4",
                            ),
                        ]
                    )
                ]
            ),
            # Upload area
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                "📤 Upload Data Files", className="mb-0"
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Upload(
                                                id="upload-data",
                                                max_size=dynamic_config.get_max_upload_size_bytes(),  # Updated to use new method
                                                children=html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-cloud-upload-alt fa-4x mb-3 text-primary"
                                                        ),
                                                        html.H5(
                                                            "Drag and Drop or Click to Upload",
                                                            className="text-primary",
                                                        ),
                                                        html.P(
                                                            "Supports CSV, Excel (.xlsx, .xls), and JSON files",
                                                            className="text-muted mb-0",
                                                        ),
                                                    ]
                                                ),
                                                style={
                                                    "width": "100%",
                                                    "border": "2px dashed #007bff",
                                                    "borderRadius": "8px",
                                                    "textAlign": "center",
                                                    "cursor": "pointer",
                                                    "backgroundColor": "#f8f9fa",
                                                },
                                                multiple=True,
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ]
                    )
                ]
            ),
            # Upload results area
            dbc.Row([dbc.Col([html.Div(id="upload-results")])], className="mb-4"),
            # Data preview area
            dbc.Row([dbc.Col([html.Div(id="file-preview")])]),
            # Navigation to analytics
            dbc.Row([dbc.Col([html.Div(id="upload-nav")])]),
            # Container for toast notifications
            html.Div(id="toast-container"),
            # CRITICAL: Hidden placeholder buttons to prevent callback errors
            html.Div(
                [
                    dbc.Button(
                        "", id="verify-columns-btn-simple", style={"display": "none"}
                    ),
                    dbc.Button(
                        "", id="classify-devices-btn", style={"display": "none"}
                    ),
                ],
                style={"display": "none"},
            ),
            # Store for uploaded data info
            dcc.Store(id="file-info-store", data={}),
            dcc.Store(id="current-file-info-store"),
            dcc.Store(id="current-session-id", data="session_123"),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Column Mapping")),
                    dbc.ModalBody("Configure column mappings here", id="modal-body"),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel", id="column-verify-cancel", color="secondary"
                            ),
                            dbc.Button(
                                "Confirm", id="column-verify-confirm", color="success"
                            ),
                        ]
                    ),
                ],
                id="column-verification-modal",
                is_open=False,
                size="xl",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Device Classification")),
                    dbc.ModalBody("", id="device-modal-body"),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel", id="device-verify-cancel", color="secondary"
                            ),
                            dbc.Button(
                                "Confirm", id="device-verify-confirm", color="success"
                            ),
                        ]
                    ),
                ],
                id="device-verification-modal",
                is_open=False,
                size="xl",
            ),
        ],
        fluid=True,
    )


def get_uploaded_data() -> Dict[str, pd.DataFrame]:
    """Get all uploaded data (for use by analytics)."""
    return _uploaded_data_store.get_all_data()


def get_uploaded_filenames() -> List[str]:
    """Get list of uploaded filenames."""
    return _uploaded_data_store.get_filenames()


def clear_uploaded_data():
    """Clear all uploaded data."""
    _uploaded_data_store.clear_all()
    logger.info("Uploaded data cleared")


def get_file_info() -> Dict[str, Dict[str, Any]]:
    """Get information about uploaded files."""
    return _uploaded_data_store.get_file_info()


class Callbacks:
    """Container object for upload page callbacks."""

    def highlight_upload_area(self, n_clicks):
        """Highlight upload area when 'upload more' is clicked."""
        if n_clicks:
            return {
                "width": "100%",
                "border": "3px dashed #28a745",
                "borderRadius": "8px",
                "textAlign": "center",
                "cursor": "pointer",
                "backgroundColor": "#d4edda",
                "animation": "pulse 1s infinite",
            }
        return {
            "width": "100%",
            "border": "2px dashed #007bff",
            "borderRadius": "8px",
            "textAlign": "center",
            "cursor": "pointer",
            "backgroundColor": "#f8f9fa",
        }

    def restore_upload_state(self, pathname: str):
        """Return stored upload details when revisiting the upload page."""

        if pathname != "/file-upload" or not _uploaded_data_store:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        upload_results: List[Any] = []
        file_preview_components: List[Any] = []
        current_file_info: Dict[str, Any] = {}

        for filename, df in _uploaded_data_store.get_all_data().items():
            rows = len(df)
            cols = len(df.columns)

            upload_results.append(
                build_success_alert(
                    filename,
                    rows,
                    cols,
                    prefix="Previously uploaded:",
                    processed=False,
                )
            )

            file_preview_components.append(build_file_preview_component(df, filename))

            current_file_info = {
                "filename": filename,
                "rows": rows,
                "columns": cols,
                "column_names": df.columns.tolist(),
                "ai_suggestions": generate_column_suggestions(df.columns.tolist()),
            }

        upload_nav = html.Div(
            [
                html.Hr(),
                html.H5("Ready to analyze?"),
                dbc.Button(
                    "🚀 Go to Analytics", href="/analytics", color="success", size="lg"
                ),
            ]
        )

        return (
            upload_results,
            file_preview_components,
            {},
            upload_nav,
            current_file_info,
            False,
            False,
        )

    def process_uploaded_files(
        self, contents_list: List[str] | str, filenames_list: List[str] | str
    ) -> Tuple[Any, Any, Any, Any, Any, Any, Any]:
        """Handle new uploads and store data in the upload store."""

        if not contents_list:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        _uploaded_data_store.clear_all()

        if not isinstance(contents_list, list):
            contents_list = [contents_list]
        if not isinstance(filenames_list, list):
            filenames_list = [filenames_list]

        upload_results: List[Any] = []
        file_preview_components: List[Any] = []
        file_info_dict: Dict[str, Any] = {}
        current_file_info: Dict[str, Any] = {}

        file_parts: Dict[str, List[str]] = {}

        for content, filename in zip(contents_list, filenames_list):
            file_parts.setdefault(filename, []).append(content)

        for filename, parts in file_parts.items():
            if len(parts) > 1:
                prefix, first = parts[0].split(",", 1)
                combined_data = first
                for part in parts[1:]:
                    _pfx, data = part.split(",", 1)
                    combined_data += data
                content = f"{prefix},{combined_data}"
            else:
                content = parts[0]

            try:
                result = process_uploaded_file(content, filename)

                if result["success"]:
                    df = result["data"]
                    rows = len(df)
                    cols = len(df.columns)

                    _uploaded_data_store.add_file(filename, df)

                    upload_results.append(build_success_alert(filename, rows, cols))

                    file_preview_components.append(
                        build_file_preview_component(df, filename)
                    )

                    column_names = df.columns.tolist()
                    file_info_dict[filename] = {
                        "filename": filename,
                        "rows": rows,
                        "columns": cols,
                        "column_names": column_names,
                        "upload_time": result["upload_time"].isoformat(),
                        "ai_suggestions": generate_column_suggestions(column_names),
                    }
                    current_file_info = file_info_dict[filename]

                    try:
                        learning_service = get_device_learning_service()
                        user_mappings = learning_service.get_user_device_mappings(
                            filename
                        )
                        if user_mappings:
                            from services.ai_mapping_store import ai_mapping_store

                            ai_mapping_store.clear()
                            for device, mapping in user_mappings.items():
                                mapping["source"] = "user_confirmed"
                                ai_mapping_store.set(device, mapping)
                            logger.info(
                                f"✅ Loaded {len(user_mappings)} saved mappings - AI SKIPPED"
                            )
                        else:
                            logger.info("🆕 First upload - AI will be used")
                            from services.ai_mapping_store import ai_mapping_store

                            ai_mapping_store.clear()
                            # Try to auto-apply learned mappings
                            auto_apply_learned_mappings(df, filename)
                    except Exception as e:  # pragma: no cover - best effort
                        logger.info(f"⚠️ Error: {e}")

                else:
                    upload_results.append(build_failure_alert(result["error"]))

            except Exception as e:  # pragma: no cover - best effort
                upload_results.append(
                    build_failure_alert(f"Error processing {filename}: {str(e)}")
                )

        upload_nav = []
        if file_info_dict:
            upload_nav = html.Div(
                [
                    html.Hr(),
                    html.H5("Ready to analyze?"),
                    dbc.Button(
                        "🚀 Go to Analytics",
                        href="/analytics",
                        color="success",
                        size="lg",
                    ),
                ]
            )

        return (
            upload_results,
            file_preview_components,
            file_info_dict,
            upload_nav,
            current_file_info,
            no_update,
            no_update,
        )

    def handle_modal_dialogs(
        self,
        verify_clicks: int | None,
        classify_clicks: int | None,
        confirm_clicks: int | None,
        cancel_col_clicks: int | None,
        cancel_dev_clicks: int | None,
    ) -> Tuple[Any, Any, Any]:
        """Open/close verification modals and show success toasts."""

        trigger_id = get_trigger_id()

        if "verify-columns-btn-simple" in trigger_id and verify_clicks:
            return no_update, True, no_update

        if "classify-devices-btn" in trigger_id and classify_clicks:
            return no_update, no_update, True

        if "column-verify-confirm" in trigger_id and confirm_clicks:
            return no_update, False, no_update

        if "column-verify-cancel" in trigger_id or "device-verify-cancel" in trigger_id:
            return no_update, False, False

        return no_update, no_update, no_update

    def apply_ai_suggestions(self, n_clicks, file_info):
        """Apply AI suggestions automatically."""
        if not n_clicks or not file_info:
            return [no_update]

        ai_suggestions = file_info.get("ai_suggestions", {})
        columns = file_info.get("columns", [])

        logger.info(f"🤖 Applying AI suggestions for {len(columns)} columns")

        suggested_values = []
        for column in columns:
            suggestion = ai_suggestions.get(column, {})
            confidence = suggestion.get("confidence", 0.0)
            field = suggestion.get("field", "")

            if confidence > 0.3 and field:
                suggested_values.append(field)
                logger.info(f"   ✅ {column} -> {field} ({confidence:.0%})")
            else:
                suggested_values.append(None)
                logger.info(
                    f"   ❓ {column} -> No confident suggestion ({confidence:.0%})"
                )

        return [suggested_values]

    def populate_device_modal_with_learning(self, is_open, file_info):
        """Populate the device modal with learned or AI-suggested data."""
        if not is_open:
            return "Modal closed", file_info

        logger.info("🔧 Populating device modal...")

        try:
            uploaded_data = get_uploaded_data()
            if not uploaded_data:
                return dbc.Alert("No uploaded data found", color="warning")

            all_devices = set()
            device_columns = ["door_id", "device_name", "location", "door", "device"]

            for filename, df in uploaded_data.items():
                logger.info(f"📄 Processing {filename} with {len(df)} rows")

                for col in df.columns:
                    col_lower = col.lower().strip()
                    if any(device_col in col_lower for device_col in device_columns):
                        unique_vals = df[col].dropna().unique()
                        all_devices.update(str(val) for val in unique_vals)
                        logger.info(
                            f"   Found {len(unique_vals)} devices in column '{col}'"
                        )

                        logger.debug(f"🔍 DEBUG - First 10 device names from '{col}':")
                        sample_devices = unique_vals[:10]
                        for i, device in enumerate(sample_devices, 1):
                            logger.debug(f"   {i:2d}. {device}")

                        logger.debug("🤖 DEBUG - Testing AI on sample devices:")
                        try:
                            from services.ai_device_generator import AIDeviceGenerator

                            ai_gen = AIDeviceGenerator()

                            for device in sample_devices[:5]:
                                try:
                                    result = ai_gen.generate_device_attributes(
                                        str(device)
                                    )
                                    logger.info(
                                        f"   🚪 '{device}' → Name: '{result.device_name}', Floor: {result.floor_number}, Security: {result.security_level}, Confidence: {result.confidence:.1%}"
                                    )
                                    logger.info(
                                        f"      Access: Entry={result.is_entry}, Exit={result.is_exit}, Elevator={result.is_elevator}"
                                    )
                                    logger.info(
                                        f"      Reasoning: {result.ai_reasoning}"
                                    )
                                except Exception as e:
                                    logger.info(f"   ❌ AI error on '{device}': {e}")
                        except Exception as e:
                            logger.debug(f"🤖 DEBUG - AI import error: {e}")

            actual_devices = sorted(list(all_devices))
            logger.info(f"🎯 Total unique devices found: {len(actual_devices)}")

            file_info = file_info or {}

            if not actual_devices:
                file_info["devices"] = []
                return (
                    dbc.Alert(
                        [
                            html.H6("No devices detected"),
                            html.P(
                                "No device/door columns found in uploaded data. Expected columns: door_id, device_name, location, etc."
                            ),
                        ],
                        color="warning",
                    ),
                    file_info,
                )

            table_rows = []
            for i, device_name in enumerate(actual_devices):
                ai_attributes = analyze_device_name_with_ai(device_name)

                table_rows.append(
                    html.Tr(
                        [
                            html.Td(
                                [
                                    html.Strong(device_name),
                                    html.Br(),
                                    html.Small(
                                        f"AI Confidence: {ai_attributes.get('confidence', 0.5):.0%}",
                                        className="text-success",
                                    ),
                                ]
                            ),
                            html.Td(
                                [
                                    dbc.Input(
                                        id={"type": "device-floor", "index": i},
                                        type="number",
                                        min=0,
                                        max=50,
                                        value=ai_attributes.get("floor_number", 1),
                                        placeholder="Floor",
                                        size="sm",
                                    )
                                ]
                            ),
                            html.Td(
                                dbc.Checklist(
                                    id={"type": "device-access", "index": i},
                                    options=[
                                        {"label": "Entry", "value": "is_entry"},
                                        {"label": "Exit", "value": "is_exit"},
                                        {"label": "Elevator", "value": "is_elevator"},
                                        {"label": "Stairwell", "value": "is_stairwell"},
                                        {
                                            "label": "Fire Exit",
                                            "value": "is_fire_escape",
                                        },
                                        {
                                            "label": "Restricted",
                                            "value": "is_restricted",
                                        },
                                    ],
                                    value=[
                                        key
                                        for key in [
                                            "is_entry",
                                            "is_exit",
                                            "is_elevator",
                                            "is_stairwell",
                                            "is_fire_escape",
                                            "is_restricted",
                                        ]
                                        if ai_attributes.get(
                                            key,
                                            ai_attributes.get(key.replace("is_", "")),
                                        )
                                    ],
                                    inline=False,
                                )
                            ),
                            html.Td(
                                dbc.Input(
                                    id={"type": "device-security", "index": i},
                                    type="number",
                                    min=0,
                                    max=10,
                                    value=ai_attributes.get("security_level", 5),
                                    placeholder="0-10",
                                    size="sm",
                                )
                            ),
                        ]
                    )
                )

            file_info = file_info or {}
            file_info["devices"] = actual_devices

            return (
                dbc.Container(
                    [
                        dbc.Alert(
                            [
                                html.Strong("🤖 AI Analysis: "),
                                f"Analyzed {len(actual_devices)} devices. Check console for detailed AI debug info.",
                            ],
                            color="info",
                            className="mb-3",
                        ),
                        dbc.Table(
                            [
                                html.Thead(
                                    [
                                        html.Tr(
                                            [
                                                html.Th("Device Name"),
                                                html.Th("Floor"),
                                                html.Th("Access Types"),
                                                html.Th("Security Level"),
                                            ]
                                        )
                                    ]
                                ),
                                html.Tbody(table_rows),
                            ],
                            striped=True,
                            hover=True,
                        ),
                    ]
                ),
                file_info,
            )

        except Exception as e:  # pragma: no cover - safety net
            logger.info(f"❌ Error in device modal: {e}")
            return dbc.Alert(f"Error: {e}", color="danger"), file_info

    def populate_modal_content(self, is_open, file_info):
        """Generate the column mapping modal content."""

        if not is_open or not file_info:
            return (
                "Modal closed"
                if not is_open
                else dbc.Alert("No file information available", color="warning")
            )

        filename = (
            str(file_info.get("filename", "Unknown"))
            .replace("⛑️", "")
            .replace("🔧", "")
            .replace("❌", "")
        )
        columns = file_info.get("column_names", []) or file_info.get("columns", [])
        ai_suggestions = file_info.get("ai_suggestions", {})

        if not columns:
            return dbc.Alert(f"No columns found in {filename}", color="warning")

        standard_fields = [
            {
                "field": "person_id",
                "label": "Person/User ID",
                "description": "Identifies who accessed",
            },
            {
                "field": "door_id",
                "label": "Door/Location ID",
                "description": "Identifies where access occurred",
            },
            {
                "field": "timestamp",
                "label": "Timestamp",
                "description": "When access occurred",
            },
            {
                "field": "access_result",
                "label": "Access Result",
                "description": "Success/failure of access",
            },
            {
                "field": "token_id",
                "label": "Token/Badge ID",
                "description": "Badge or card identifier",
            },
            {
                "field": "device_status",
                "label": "Device Status",
                "description": "Status of access device",
            },
            {
                "field": "entry_type",
                "label": "Entry/Exit Type",
                "description": "Direction of access",
            },
        ]

        csv_column_options: List[Dict[str, str]] = [
            {"label": f'"{col}"', "value": col} for col in columns
        ]
        csv_column_options.append({"label": "Skip this field", "value": "skip"})

        table_rows = []
        for standard_field in standard_fields:
            field_name = standard_field["field"]

            suggested_csv_column = None
            ai_confidence = 0.0
            for csv_col, suggestion in ai_suggestions.items():
                if suggestion.get("field") == field_name:
                    suggested_csv_column = csv_col
                    ai_confidence = suggestion.get("confidence", 0.0)
                    break

            table_rows.append(
                html.Tr(
                    [
                        html.Td(
                            [
                                html.Strong(standard_field["label"]),
                                html.Br(),
                                html.Small(
                                    standard_field["description"],
                                    className="text-muted",
                                ),
                                html.Br(),
                                html.Code(
                                    field_name,
                                    className="bg-info text-white px-2 py-1 rounded small",
                                ),
                            ],
                            style={"width": "40%"},
                        ),
                        html.Td(
                            [
                                dcc.Dropdown(
                                    id={
                                        "type": "standard-field-mapping",
                                        "field": field_name,
                                    },
                                    options=csv_column_options,
                                    placeholder=f"Select CSV column for {field_name}",
                                    value=suggested_csv_column,
                                    style={"minWidth": "200px"},
                                )
                            ],
                            style={"width": "50%"},
                        ),
                        html.Td(
                            [
                                dbc.Badge(
                                    (
                                        f"AI: {ai_confidence:.0%}"
                                        if suggested_csv_column
                                        else "No AI suggestion"
                                    ),
                                    color=(
                                        "success"
                                        if ai_confidence > 0.7
                                        else (
                                            "warning"
                                            if ai_confidence > 0.4
                                            else "secondary"
                                        )
                                    ),
                                    className="small",
                                )
                            ],
                            style={"width": "10%"},
                        ),
                    ]
                )
            )

        return [
            dbc.Alert(
                [
                    html.H6(
                        f"Map Analytics Fields to CSV Columns from {filename}",
                        className="mb-2",
                    ),
                    html.P(
                        [
                            "Your CSV has these columns: ",
                            ", ".join([col for col in columns[:5]]),
                            f"{'...' if len(columns) > 5 else ''}",
                        ],
                        className="mb-2",
                    ),
                    html.P(
                        [
                            html.Strong("Instructions: "),
                            "Each row below represents a field that our analytics system expects. ",
                            "Select which column from your CSV file should provide the data for each field.",
                        ],
                        className="mb-0",
                    ),
                ],
                color="primary",
                className="mb-3",
            ),
            dbc.Table(
                [
                    html.Thead(
                        [
                            html.Tr(
                                [
                                    html.Th(
                                        "Analytics Field (Fixed)",
                                        style={"width": "40%"},
                                    ),
                                    html.Th(
                                        "Maps to CSV Column (Variable)",
                                        style={"width": "50%"},
                                    ),
                                    html.Th("AI Confidence", style={"width": "10%"}),
                                ]
                            )
                        ]
                    ),
                    html.Tbody(table_rows),
                ],
                striped=True,
                hover=True,
            ),
            dbc.Card(
                [
                    dbc.CardHeader(html.H6("Your CSV Columns", className="mb-0")),
                    dbc.CardBody(
                        [
                            html.P("Available columns from your uploaded file:"),
                            html.Div(
                                [
                                    dbc.Badge(
                                        col,
                                        color="light",
                                        text_color="dark",
                                        className="me-1 mb-1",
                                    )
                                    for col in columns
                                ]
                            ),
                        ]
                    ),
                ],
                className="mt-3",
            ),
        ]

    def save_confirmed_device_mappings(
        self, confirm_clicks, floors, security, access, special, file_info
    ) -> Tuple[Any, Any, Any]:
        """Save confirmed device mappings to database."""

        if not confirm_clicks or not file_info:
            return no_update, no_update, no_update

        try:
            devices = file_info.get("devices", [])
            filename = file_info.get("filename", "")

            user_mappings = {}
            for i, device in enumerate(devices):
                user_mappings[device] = {
                    "floor_number": floors[i] if i < len(floors) else 1,
                    "security_level": security[i] if i < len(security) else 5,
                    "is_entry": "entry" in (access[i] if i < len(access) else []),
                    "is_exit": "exit" in (access[i] if i < len(access) else []),
                    "is_restricted": "is_restricted"
                    in (special[i] if i < len(special) else []),
                    "confidence": 1.0,
                    "device_name": device,
                    "source": "user_confirmed",
                    "saved_at": datetime.now().isoformat(),
                }

            learning_service = get_device_learning_service()
            df = _uploaded_data_store.get_all_data().get(filename)
            learning_service.save_user_device_mappings(df, filename, user_mappings)

            from services.ai_mapping_store import ai_mapping_store

            ai_mapping_store.update(user_mappings)

            logger.info(
                f"\u2705 Saved {len(user_mappings)} confirmed device mappings to database"
            )

            success_alert = dbc.Toast(
                "✅ Device mappings saved to database!",
                header="Confirmed & Saved",
                is_open=True,
                dismissable=True,
                duration=3000,
            )

            return success_alert, False, False

        except Exception as e:
            logger.info(f"\u274c Error saving device mappings: {e}")
            error_alert = dbc.Toast(
                f"❌ Error saving mappings: {e}",
                header="Error",
                is_open=True,
                dismissable=True,
                duration=5000,
            )
            return error_alert, no_update, no_update

    def save_verified_column_mappings(
        self, confirm_clicks, values, ids, file_info
    ) -> Any:
        """Persist verified column mappings using learning service."""

        if not confirm_clicks or not file_info:
            return no_update

        try:
            filename = file_info.get("filename", "")
            column_mappings = {}
            for comp_id, val in zip(ids, values):
                field = comp_id.get("field") if isinstance(comp_id, dict) else None
                if field and val and val != "skip":
                    column_mappings[field] = val

            save_verified_mappings(filename, column_mappings, file_info)

            try:
                from services.consolidated_learning_service import get_learning_service

                df = _uploaded_data_store.get_all_data().get(filename)
                if df is not None:
                    get_learning_service().save_complete_mapping(
                        df, filename, {}, column_mappings
                    )
            except Exception as e:
                logger.debug(f"Learning service save failed: {e}")

            return dbc.Toast(
                "✅ Column mappings saved!",
                header="Saved",
                is_open=True,
                dismissable=True,
                duration=3000,
            )

        except Exception as e:
            logger.info(f"❌ Error saving column mappings: {e}")
            return dbc.Toast(
                f"❌ Error saving mappings: {e}",
                header="Error",
                is_open=True,
                dismissable=True,
                duration=5000,
            )


def get_trigger_id() -> str:
    """Return the triggered callback identifier."""
    ctx = callback_context
    return ctx.triggered[0]["prop_id"] if ctx.triggered else ""


def save_ai_training_data(filename: str, mappings: Dict[str, str], file_info: Dict):
    """Save confirmed mappings for AI training"""
    try:
        logger.info(f"🤖 Saving AI training data for {filename}")

        # Prepare training data
        training_data = {
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "mappings": mappings,
            "reverse_mappings": {v: k for k, v in mappings.items()},
            "column_count": len(file_info.get("columns", [])),
            "ai_suggestions": file_info.get("ai_suggestions", {}),
            "user_verified": True,
        }

        try:
            from plugins.ai_classification.plugin import AIClassificationPlugin
            from plugins.ai_classification.config import get_ai_config

            ai_plugin = AIClassificationPlugin(get_ai_config())
            if ai_plugin.start():
                session_id = (
                    f"verified_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                ai_mappings = {v: k for k, v in mappings.items()}
                ai_plugin.confirm_column_mapping(ai_mappings, session_id)
                logger.info(f"✅ AI training data saved: {ai_mappings}")
        except Exception as ai_e:
            logger.info(f"⚠️ AI training save failed: {ai_e}")

        import os

        os.makedirs("data/training", exist_ok=True)
        with open(
            f"data/training/mappings_{datetime.now().strftime('%Y%m%d')}.jsonl",
            "a",
            encoding="utf-8",
            errors="replace",
        ) as f:
            f.write(json.dumps(training_data) + "\n")

        logger.info(f"✅ Training data saved locally")

    except Exception as e:
        logger.info(f"❌ Error saving training data: {e}")


# ------------------------------------------------------------
# Callback manager for the upload page
# ------------------------------------------------------------


def register_callbacks(
    manager: UnifiedCallbackCoordinator,
    controller: UnifiedAnalyticsController | None = None,
) -> None:
    """Instantiate :class:`Callbacks` and register its methods."""

    cb = Callbacks()
    callback_defs = [
        (
            cb.highlight_upload_area,
            Output("upload-data", "style"),
            Input("upload-more-btn", "n_clicks"),
            None,
            "highlight_upload_area",
            {"prevent_initial_call": True},
        ),
        (
            cb.restore_upload_state,
            [
                Output("upload-results", "children", allow_duplicate=True),
                Output("file-preview", "children", allow_duplicate=True),
                Output("file-info-store", "data", allow_duplicate=True),
                Output("upload-nav", "children", allow_duplicate=True),
                Output("current-file-info-store", "data", allow_duplicate=True),
                Output("column-verification-modal", "is_open", allow_duplicate=True),
                Output("device-verification-modal", "is_open", allow_duplicate=True),
            ],
            Input("url", "pathname"),
            None,
            "restore_upload_state",
            {"prevent_initial_call": "initial_duplicate", "allow_duplicate": True},
        ),
        (
            cb.process_uploaded_files,
            [
                Output("upload-results", "children", allow_duplicate=True),
                Output("file-preview", "children", allow_duplicate=True),
                Output("file-info-store", "data", allow_duplicate=True),
                Output("upload-nav", "children", allow_duplicate=True),
                Output("current-file-info-store", "data", allow_duplicate=True),
                Output("column-verification-modal", "is_open", allow_duplicate=True),
                Output("device-verification-modal", "is_open", allow_duplicate=True),
            ],
            Input("upload-data", "contents"),
            State("upload-data", "filename"),
            "process_uploaded_files",
            {"prevent_initial_call": True, "allow_duplicate": True},
        ),
        (
            cb.handle_modal_dialogs,
            [
                Output("toast-container", "children", allow_duplicate=True),
                Output("column-verification-modal", "is_open", allow_duplicate=True),
                Output("device-verification-modal", "is_open", allow_duplicate=True),
            ],
            [
                Input("verify-columns-btn-simple", "n_clicks"),
                Input("classify-devices-btn", "n_clicks"),
                Input("column-verify-confirm", "n_clicks"),
                Input("column-verify-cancel", "n_clicks"),
                Input("device-verify-cancel", "n_clicks"),
            ],
            None,
            "handle_modal_dialogs",
            {"prevent_initial_call": True, "allow_duplicate": True},
        ),
        (
            cb.apply_ai_suggestions,
            [Output({"type": "column-mapping", "index": ALL}, "value")],
            [Input("column-verify-ai-auto", "n_clicks")],
            [State("current-file-info-store", "data")],
            "apply_ai_suggestions",
            {"prevent_initial_call": True},
        ),
        (
            cb.populate_device_modal_with_learning,
            [
                Output("device-modal-body", "children"),
                Output("current-file-info-store", "data", allow_duplicate=True),
            ],
            Input("device-verification-modal", "is_open"),
            State("current-file-info-store", "data"),
            "populate_device_modal_with_learning",
            {"prevent_initial_call": True, "allow_duplicate": True},
        ),
        (
            cb.populate_modal_content,
            Output("modal-body", "children"),
            [
                Input("column-verification-modal", "is_open"),
                Input("current-file-info-store", "data"),
            ],
            None,
            "populate_modal_content",
            {"prevent_initial_call": True},
        ),
        (
            cb.save_confirmed_device_mappings,
            [
                Output("toast-container", "children", allow_duplicate=True),
                Output("column-verification-modal", "is_open", allow_duplicate=True),
                Output("device-verification-modal", "is_open", allow_duplicate=True),
            ],
            [Input("device-verify-confirm", "n_clicks")],
            [
                State({"type": "device-floor", "index": ALL}, "value"),
                State({"type": "device-security", "index": ALL}, "value"),
                State({"type": "device-access", "index": ALL}, "value"),
                State({"type": "device-special", "index": ALL}, "value"),
                State("current-file-info-store", "data"),
            ],
            "save_confirmed_device_mappings",
            {"prevent_initial_call": True},
        ),
        (
            cb.save_verified_column_mappings,
            Output("toast-container", "children", allow_duplicate=True),
            [Input("column-verify-confirm", "n_clicks")],
            [
                State({"type": "standard-field-mapping", "field": ALL}, "value"),
                State({"type": "standard-field-mapping", "field": ALL}, "id"),
                State("current-file-info-store", "data"),
            ],
            "save_verified_column_mappings",
            {"prevent_initial_call": True, "allow_duplicate": True},
        ),
    ]

    for func, outputs, inputs, states, cid, extra in callback_defs:
        manager.register_callback(
            outputs,
            inputs,
            states,
            callback_id=cid,
            component_name="file_upload",
            **extra,
        )(func)

    if controller is not None:
        controller.register_callback(
            "on_analysis_error",
            lambda aid, err: logger.error("File upload error: %s", err),
        )


# Export functions for integration with other modules
__all__ = [
    "layout",
    "Callbacks",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "save_ai_training_data",
    "register_callbacks",
]

logger.info(f"\U0001f50d FILE_UPLOAD.PY LOADED - Callbacks should be registered")
