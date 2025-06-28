#!/usr/bin/env python3
"""
Complete File Upload Page - Missing piece for consolidation
Integrates with analytics system
"""
import logging
import base64
import io
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from typing import Optional, Dict, Any, List
from dash import html, dcc
from dash.dash import no_update
from dash._callback_context import callback_context
from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
from services.device_learning_service import DeviceLearningService

from components.column_verification import (
    save_verified_mappings,
)


logger = logging.getLogger(__name__)

# Initialize device learning service
learning_service = DeviceLearningService()


# -----------------------------------------------------------------------------
# Persistent Uploaded Data Store
# -----------------------------------------------------------------------------
class UploadedDataStore:
    """Persistent uploaded data store with file system backup."""

    def __init__(self) -> None:
        self._data_store: Dict[str, pd.DataFrame] = {}
        self._file_info_store: Dict[str, Dict[str, Any]] = {}
        self.storage_dir = Path("temp/uploaded_data")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._load_from_disk()

    # -- Internal helpers ---------------------------------------------------
    def _get_file_path(self, filename: str) -> Path:
        safe_name = filename.replace(" ", "_").replace("/", "_")
        return self.storage_dir / f"{safe_name}.pkl"

    def _info_path(self) -> Path:
        return self.storage_dir / "file_info.json"

    def _load_from_disk(self) -> None:
        try:
            if self._info_path().exists():
                with open(self._info_path(), "r") as f:
                    self._file_info_store = json.load(f)
            for fname in self._file_info_store.keys():
                fpath = self._get_file_path(fname)
                if fpath.exists():
                    df = pd.read_pickle(fpath)
                    self._data_store[fname] = df
                    logger.info(f"Loaded {fname} from disk")
        except Exception as e:  # pragma: no cover - best effort
            logger.error(f"Error loading uploaded data: {e}")

    def _save_to_disk(self, filename: str, df: pd.DataFrame) -> None:
        try:
            df.to_pickle(self._get_file_path(filename))
            self._file_info_store[filename] = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "upload_time": datetime.now().isoformat(),
                "size_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            }
            with open(self._info_path(), "w") as f:
                json.dump(self._file_info_store, f, indent=2)
        except Exception as e:  # pragma: no cover - best effort
            logger.error(f"Error saving uploaded data: {e}")

    # -- Public API ---------------------------------------------------------
    def add_file(self, filename: str, df: pd.DataFrame) -> None:
        self._data_store[filename] = df
        self._save_to_disk(filename, df)

    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        return self._data_store.copy()

    def get_filenames(self) -> List[str]:
        return list(self._data_store.keys())

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return self._file_info_store.copy()

    def clear_all(self) -> None:
        self._data_store.clear()
        self._file_info_store.clear()
        try:
            for pkl in self.storage_dir.glob("*.pkl"):
                pkl.unlink()
            if self._info_path().exists():
                self._info_path().unlink()
        except Exception as e:  # pragma: no cover - best effort
            logger.error(f"Error clearing uploaded data: {e}")


# Global persistent storage
_uploaded_data_store = UploadedDataStore()


def analyze_device_name_with_ai(device_name):
    """User mappings ALWAYS override AI - FIXED"""
    try:
        from components.simple_device_mapping import _device_ai_mappings

        # Check for user-confirmed mapping first
        if device_name in _device_ai_mappings:
            mapping = _device_ai_mappings[device_name]
            if mapping.get("source") == "user_confirmed":
                print(f"\U0001f512 Using USER CONFIRMED mapping for '{device_name}'")
                return mapping

        # Only use AI if no user mapping exists
        print(f"\U0001f916 No user mapping found, generating AI analysis for '{device_name}'")

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
        print(f"\u274c Error in device analysis: {e}")
        return {
            "floor_number": 1,
            "security_level": 5,
            "confidence": 0.1,
            "source": "fallback",
        }


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


def process_uploaded_file(contents, filename):
    """Process uploaded file content"""
    try:
        # Decode the base64 encoded file content
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)

        # Determine file type and parse accordingly
        if filename.endswith(".csv"):
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(decoded))
        elif filename.endswith(".json"):
            # Fix for JSON processing to ensure DataFrame is returned
            try:
                json_data = json.loads(decoded.decode("utf-8"))

                # Handle different JSON structures
                if isinstance(json_data, list):
                    df = pd.DataFrame(json_data)
                elif isinstance(json_data, dict):
                    if "data" in json_data:
                        df = pd.DataFrame(json_data["data"])
                    else:
                        df = pd.DataFrame([json_data])
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported JSON structure: {type(json_data)}",
                    }
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON format: {str(e)}"}
        else:
            return {
                "success": False,
                "error": f"Unsupported file type. Supported: .csv, .json, .xlsx, .xls",
            }

        # Validate the DataFrame
        if not isinstance(df, pd.DataFrame):
            return {
                "success": False,
                "error": f"Processing resulted in {type(df)} instead of DataFrame",
            }

        if df.empty:
            return {"success": False, "error": "File contains no data"}

        return {
            "success": True,
            "data": df,
            "rows": len(df),
            "columns": list(df.columns),
            "upload_time": datetime.now(),
        }

    except Exception as e:
        return {"success": False, "error": f"Error processing file: {str(e)}"}


def create_file_preview(df: pd.DataFrame, filename: str) -> dbc.Card | dbc.Alert:
    """Create preview component for uploaded file"""
    try:
        # Basic statistics
        num_rows, num_cols = df.shape

        # Column info
        column_info = []
        for col in df.columns[:10]:  # Show first 10 columns
            dtype = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            column_info.append(f"{col} ({dtype}) - {null_count} nulls")

        return dbc.Card(
            [
                dbc.CardHeader([html.H6(f"📄 {filename}", className="mb-0")]),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H6(
                                            "File Statistics:", className="text-primary"
                                        ),
                                        html.Ul(
                                            [
                                                html.Li(f"Rows: {num_rows:,}"),
                                                html.Li(f"Columns: {num_cols}"),
                                                html.Li(
                                                    f"Memory usage: {df.memory_usage(deep=True).sum() / 1024:.1f} KB"
                                                ),
                                            ]
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        html.H6("Columns:", className="text-primary"),
                                        html.Ul(
                                            [html.Li(info) for info in column_info]
                                        ),
                                    ],
                                    width=6,
                                ),
                            ]
                        ),
                        html.Hr(),
                        html.H6("Sample Data:", className="text-primary mt-3"),
                        dbc.Table.from_dataframe(  # type: ignore[attr-defined]
                            df.head(5),
                            striped=True,
                            bordered=True,
                            hover=True,
                            responsive=True,
                            size="sm",
                        ),
                    ]
                ),
            ],
            className="mb-3",
        )

    except Exception as e:
        logger.error(f"Error creating preview for {filename}: {e}")
        return dbc.Alert(f"Error creating preview: {str(e)}", color="warning")


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


def get_ai_column_suggestions(columns: List[str]) -> Dict[str, Dict[str, Any]]:
    """Generate AI suggestions for column mapping"""
    suggestions = {}

    for col in columns:
        col_lower = col.lower().strip()

        if any(word in col_lower for word in ["time", "date", "stamp"]):
            suggestions[col] = {"field": "timestamp", "confidence": 0.8}
        elif any(word in col_lower for word in ["person", "user", "employee"]):
            suggestions[col] = {"field": "person_id", "confidence": 0.7}
        elif any(word in col_lower for word in ["door", "location", "device"]):
            suggestions[col] = {"field": "door_id", "confidence": 0.7}
        elif any(word in col_lower for word in ["access", "result", "status"]):
            suggestions[col] = {"field": "access_result", "confidence": 0.6}
        elif any(word in col_lower for word in ["token", "badge", "card"]):
            suggestions[col] = {"field": "token_id", "confidence": 0.6}
        else:
            suggestions[col] = {"field": "", "confidence": 0.0}

    return suggestions


def get_file_info() -> Dict[str, Dict[str, Any]]:
    """Get information about uploaded files."""
    return _uploaded_data_store.get_file_info()


def highlight_upload_area(n_clicks):
    """Highlight upload area when 'upload more' is clicked"""
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
def consolidated_upload_callback(
    contents_list, verify_clicks, classify_clicks, confirm_clicks,
    cancel_col_clicks, cancel_dev_clicks, confirm_dev_clicks, pathname,
    filenames_list, dropdown_values, dropdown_ids, file_info,
    col_modal_open, dev_modal_open
):
    """Single consolidated callback that handles both upload and page restoration"""

    ctx = callback_context

    # Handle page load restoration FIRST
    if not ctx.triggered or ctx.triggered[0]['prop_id'] == 'url.pathname':
        if pathname == "/file-upload" and _uploaded_data_store:
            print(f"🔄 Restoring upload state for {len(_uploaded_data_store.get_filenames())} files")

            upload_results = []
            file_preview_components = []
            current_file_info = {}

            for filename, df in _uploaded_data_store.get_all_data().items():
                rows = len(df)
                cols = len(df.columns)

                upload_results.append(
                    dbc.Alert([
                        html.H6([
                            html.I(className="fas fa-check-circle me-2"),
                            f"Previously uploaded: {filename}"
                        ], className="alert-heading"),
                        html.P(f"📊 {rows:,} rows × {cols} columns"),
                    ], color="success", className="mb-3")
                )

                preview_df = df.head(5)
                file_preview_components.append(
                    html.Div([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H6(f"📄 Data Preview: {filename}", className="mb-0")
                            ]),
                            dbc.CardBody([
                                html.H6("First 5 rows:"),
                                dbc.Table.from_dataframe(  # type: ignore[attr-defined]
                                    preview_df, striped=True, bordered=True, hover=True, size="sm"
                                ),
                                html.Hr(),
                                html.P([
                                    html.Strong("Columns: "),
                                    ", ".join(df.columns.tolist()[:10]),
                                    "..." if len(df.columns) > 10 else ""
                                ]),
                            ])
                        ], className="mb-3"),

                        dbc.Card([
                            dbc.CardHeader([html.H6("📋 Data Configuration", className="mb-0")]),
                            dbc.CardBody([
                                html.P("Configure your data for analysis:", className="mb-3"),
                                dbc.ButtonGroup([
                                    dbc.Button("📋 Verify Columns", id="verify-columns-btn-simple", color="primary", size="sm"),
                                    dbc.Button("🤖 Classify Devices", id="classify-devices-btn", color="info", size="sm"),
                                ], className="w-100"),
                            ])
                        ], className="mb-3")
                    ])
                )

                current_file_info = {
                    "filename": filename,
                    "rows": rows,
                    "columns": cols,
                    "column_names": df.columns.tolist(),
                    "ai_suggestions": get_ai_column_suggestions(df.columns.tolist())
                }

            upload_nav = html.Div([
                html.Hr(),
                html.H5("Ready to analyze?"),
                dbc.Button("🚀 Go to Analytics", href="/analytics", color="success", size="lg")
            ])

            return upload_results, file_preview_components, {}, upload_nav, current_file_info, False, False

        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id']
    print(f"🎯 Callback triggered by: {trigger_id}")

    if "upload-data.contents" in trigger_id and contents_list:
        print("📁 Processing NEW file upload - clearing previous data...")
        _uploaded_data_store.clear_all()

        if not isinstance(contents_list, list):
            contents_list = [contents_list]
        if not isinstance(filenames_list, list):
            filenames_list = [filenames_list]

        upload_results = []
        file_preview_components = []
        file_info_dict = {}
        current_file_info = {}

        for content, filename in zip(contents_list, filenames_list):
            try:
                result = process_uploaded_file(content, filename)

                if result["success"]:
                    df = result["data"]
                    rows = len(df)
                    cols = len(df.columns)

                    _uploaded_data_store.add_file(filename, df)

                    upload_results.append(
                        dbc.Alert([
                            html.H6([
                                html.I(className="fas fa-check-circle me-2"),
                                f"Successfully uploaded {filename}"
                            ], className="alert-heading"),
                            html.P(f"📊 {rows:,} rows × {cols} columns processed"),
                        ], color="success", className="mb-3")
                    )

                    preview_df = df.head(5)
                    file_preview_components.append(
                        html.Div([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H6(f"📄 Data Preview: {filename}", className="mb-0")
                                ]),
                                dbc.CardBody([
                                    html.H6("First 5 rows:"),
                                    dbc.Table.from_dataframe(  # type: ignore[attr-defined]
                                        preview_df, striped=True, bordered=True, hover=True, size="sm"
                                    ),
                                    html.Hr(),
                                    html.P([html.Strong("Columns: "), ", ".join(df.columns.tolist()[:10])]),
                                ])
                            ], className="mb-3"),

                            dbc.Card([
                                dbc.CardHeader([html.H6("📋 Data Configuration", className="mb-0")]),
                                dbc.CardBody([
                                    html.P("Configure your data for analysis:", className="mb-3"),
                                    dbc.ButtonGroup([
                                        dbc.Button("📋 Verify Columns", id="verify-columns-btn-simple", color="primary", size="sm"),
                                        dbc.Button("🤖 Classify Devices", id="classify-devices-btn", color="info", size="sm"),
                                    ], className="w-100"),
                                ])
                            ], className="mb-3")
                        ])
                    )

                    column_names = df.columns.tolist()
                    file_info_dict[filename] = {
                        "filename": filename,
                        "rows": rows,
                        "columns": cols,
                        "column_names": column_names,
                        "upload_time": result["upload_time"].isoformat(),
                        "ai_suggestions": get_ai_column_suggestions(column_names)
                    }
                    current_file_info = file_info_dict[filename]

                    # Load saved mappings on first upload - SIMPLE FIX
                    try:
                        user_mappings = learning_service.get_user_device_mappings(filename)
                        if user_mappings:
                            from components.simple_device_mapping import _device_ai_mappings
                            _device_ai_mappings.clear()
                            # Mark all as user_confirmed to override AI
                            for device, mapping in user_mappings.items():
                                mapping["source"] = "user_confirmed"
                                _device_ai_mappings[device] = mapping
                            print(f"✅ Loaded {len(user_mappings)} saved mappings - AI SKIPPED")
                        else:
                            print(f"🆕 First upload - AI will be used")
                            # Clear any stale mappings
                            from components.simple_device_mapping import _device_ai_mappings
                            _device_ai_mappings.clear()
                    except Exception as e:
                        print(f"⚠️ Error: {e}")

                else:
                    upload_results.append(
                        dbc.Alert([
                            html.H6("Upload Failed", className="alert-heading"),
                            html.P(result["error"]),
                        ], color="danger")
                    )

            except Exception as e:
                upload_results.append(
                    dbc.Alert(f"Error processing {filename}: {str(e)}", color="danger")
                )

        upload_nav = []
        if file_info_dict:
            upload_nav = html.Div([
                html.Hr(),
                html.H5("Ready to analyze?"),
                dbc.Button("🚀 Go to Analytics", href="/analytics", color="success", size="lg")
            ])

        return upload_results, file_preview_components, file_info_dict, upload_nav, current_file_info, no_update, no_update

    elif "verify-columns-btn-simple" in trigger_id and verify_clicks:
        print("🔍 Opening column verification modal...")
        return no_update, no_update, no_update, no_update, no_update, True, no_update

    elif "classify-devices-btn" in trigger_id and classify_clicks:
        print("🤖 Opening device classification modal...")
        return no_update, no_update, no_update, no_update, no_update, no_update, True

    elif "column-verify-confirm" in trigger_id and confirm_clicks:
        print("✅ Column mappings confirmed")
        success_alert = dbc.Toast([html.P("✅ Column mappings saved!")],
                                 header="Saved", is_open=True, dismissable=True, duration=3000)
        return success_alert, no_update, no_update, no_update, no_update, False, no_update


    elif "column-verify-cancel" in trigger_id or "device-verify-cancel" in trigger_id:
        print("❌ Closing modals...")
        return no_update, no_update, no_update, no_update, no_update, False, False

    return no_update, no_update, no_update, no_update, no_update, no_update, no_update


def save_ai_training_data(filename: str, mappings: Dict[str, str], file_info: Dict):
    """Save confirmed mappings for AI training"""
    try:
        print(f"🤖 Saving AI training data for {filename}")

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
                print(f"✅ AI training data saved: {ai_mappings}")
        except Exception as ai_e:
            print(f"⚠️ AI training save failed: {ai_e}")

        import os

        os.makedirs("data/training", exist_ok=True)
        with open(
            f"data/training/mappings_{datetime.now().strftime('%Y%m%d')}.jsonl", "a"
        ) as f:
            f.write(json.dumps(training_data) + "\n")

        print(f"✅ Training data saved locally")

    except Exception as e:
        print(f"❌ Error saving training data: {e}")


def apply_ai_suggestions(n_clicks, file_info):
    """Apply AI suggestions automatically - RESTORED"""
    if not n_clicks or not file_info:
        return [no_update]

    ai_suggestions = file_info.get("ai_suggestions", {})
    columns = file_info.get("columns", [])

    print(f"🤖 Applying AI suggestions for {len(columns)} columns")

    # Apply AI suggestions with confidence > 0.3
    suggested_values = []
    for column in columns:
        suggestion = ai_suggestions.get(column, {})
        confidence = suggestion.get("confidence", 0.0)
        field = suggestion.get("field", "")

        if confidence > 0.3 and field:
            suggested_values.append(field)
            print(f"   ✅ {column} -> {field} ({confidence:.0%})")
        else:
            suggested_values.append(None)
            print(f"   ❓ {column} -> No confident suggestion ({confidence:.0%})")

    return [suggested_values]


def populate_device_modal_with_learning(is_open, file_info):
    """Fixed device modal population - gets ALL devices WITH DEBUG"""
    if not is_open:
        return "Modal closed"

    print(f"🔧 Populating device modal...")

    try:
        uploaded_data = get_uploaded_data()
        if not uploaded_data:
            return dbc.Alert("No uploaded data found", color="warning")

        all_devices = set()
        device_columns = ["door_id", "device_name", "location", "door", "device"]

        for filename, df in uploaded_data.items():
            print(f"📄 Processing {filename} with {len(df)} rows")

            for col in df.columns:
                col_lower = col.lower().strip()
                if any(device_col in col_lower for device_col in device_columns):
                    unique_vals = df[col].dropna().unique()
                    all_devices.update(str(val) for val in unique_vals)
                    print(f"   Found {len(unique_vals)} devices in column '{col}'")

                    # ADD THIS DEBUG SECTION
                    print(f"🔍 DEBUG - First 10 device names from '{col}':")
                    sample_devices = unique_vals[:10]
                    for i, device in enumerate(sample_devices, 1):
                        print(f"   {i:2d}. {device}")

                    # TEST AI on sample devices
                    print(f"🤖 DEBUG - Testing AI on sample devices:")
                    try:
                        from services.ai_device_generator import AIDeviceGenerator
                        ai_gen = AIDeviceGenerator()

                        for device in sample_devices[:5]:  # Test first 5
                            try:
                                result = ai_gen.generate_device_attributes(str(device))
                                print(
                                    f"   🚪 '{device}' → Name: '{result.device_name}', Floor: {result.floor_number}, Security: {result.security_level}, Confidence: {result.confidence:.1%}"
                                )
                                print(
                                    f"      Access: Entry={result.is_entry}, Exit={result.is_exit}, Elevator={result.is_elevator}"
                                )
                                print(f"      Reasoning: {result.ai_reasoning}")
                            except Exception as e:
                                print(f"   ❌ AI error on '{device}': {e}")
                    except Exception as e:
                        print(f"🤖 DEBUG - AI import error: {e}")

        actual_devices = sorted(list(all_devices))
        print(f"🎯 Total unique devices found: {len(actual_devices)}")

        # Rest of your existing function...
        if not actual_devices:
            return dbc.Alert(
                [
                    html.H6("No devices detected"),
                    html.P(
                        "No device/door columns found in uploaded data. Expected columns: door_id, device_name, location, etc."
                    ),
                ],
                color="warning",
            )

        # Create device mapping table (your existing table creation code)
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
                                    {"label": "Fire Exit", "value": "is_fire_escape"},
                                ],
                                value=[
                                    k
                                    for k, v in ai_attributes.items()
                                    if k
                                    in [
                                        "is_entry",
                                        "is_exit",
                                        "is_elevator",
                                        "is_stairwell",
                                        "is_fire_escape",
                                    ]
                                    and v
                                ],
                                inline=False,
                            ),
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

        # Return your existing table structure
        return dbc.Container(
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
        )

    except Exception as e:
        print(f"❌ Error in device modal: {e}")
        return dbc.Alert(f"Error: {e}", color="danger")


def populate_modal_content(is_open, file_info):
    """RESTORED: Smart AI-driven column mapping"""

    if not is_open or not file_info:
        return "Modal closed" if not is_open else dbc.Alert("No file information available", color="warning")

    # Unicode fix
    filename = str(file_info.get("filename", "Unknown")).replace("⛑️", "").replace("🔧", "").replace("❌", "")
    columns = file_info.get("column_names", []) or file_info.get("columns", [])
    ai_suggestions = file_info.get("ai_suggestions", {})

    if not columns:
        return dbc.Alert(f"No columns found in {filename}", color="warning")

    standard_fields = [
        {"field": "person_id", "label": "Person/User ID", "description": "Identifies who accessed"},
        {"field": "door_id", "label": "Door/Location ID", "description": "Identifies where access occurred"},
        {"field": "timestamp", "label": "Timestamp", "description": "When access occurred"},
        {"field": "access_result", "label": "Access Result", "description": "Success/failure of access"},
        {"field": "token_id", "label": "Token/Badge ID", "description": "Badge or card identifier"},
        {"field": "device_status", "label": "Device Status", "description": "Status of access device"},
        {"field": "entry_type", "label": "Entry/Exit Type", "description": "Direction of access"}
    ]

    csv_column_options = [{"label": f'"{col}"', "value": col} for col in columns]
    csv_column_options.append({"label": "Skip this field", "value": "skip"})

    table_rows = []
    for standard_field in standard_fields:
        field_name = standard_field["field"]

        suggested_csv_column = None
        ai_confidence = 0.0
        for csv_col, suggestion in ai_suggestions.items():
            if suggestion.get('field') == field_name:
                suggested_csv_column = csv_col
                ai_confidence = suggestion.get('confidence', 0.0)
                break

        table_rows.append(
            html.Tr([
                html.Td([
                    html.Strong(standard_field["label"]),
                    html.Br(),
                    html.Small(standard_field["description"], className="text-muted"),
                    html.Br(),
                    html.Code(field_name, className="bg-info text-white px-2 py-1 rounded small")
                ], style={"width": "40%"}),
                html.Td([
                    dcc.Dropdown(
                        id={"type": "standard-field-mapping", "field": field_name},
                        options=csv_column_options,
                        placeholder=f"Select CSV column for {field_name}",
                        value=suggested_csv_column,
                        style={"minWidth": "200px"}
                    )
                ], style={"width": "50%"}),
                html.Td([
                    dbc.Badge(
                        f"AI: {ai_confidence:.0%}" if suggested_csv_column else "No AI suggestion",
                        color="success" if ai_confidence > 0.7 else "warning" if ai_confidence > 0.4 else "secondary",
                        className="small"
                    )
                ], style={"width": "10%"})
            ])
        )

    return [
        dbc.Alert([
            html.H6(f"Map Analytics Fields to CSV Columns from {filename}", className="mb-2"),
            html.P([
                "Your CSV has these columns: ",
                ", ".join([col for col in columns[:5]]),
                f"{'...' if len(columns) > 5 else ''}"
            ], className="mb-2"),
            html.P([
                html.Strong("Instructions: "),
                "Each row below represents a field that our analytics system expects. ",
                "Select which column from your CSV file should provide the data for each field."
            ], className="mb-0")
        ], color="primary", className="mb-3"),

        dbc.Table([
            html.Thead([
                html.Tr([
                    html.Th("Analytics Field (Fixed)", style={"width": "40%"}),
                    html.Th("Maps to CSV Column (Variable)", style={"width": "50%"}),
                    html.Th("AI Confidence", style={"width": "10%"})
                ])
            ]),
            html.Tbody(table_rows)
        ], striped=True, hover=True),

        dbc.Card([
            dbc.CardHeader(html.H6("Your CSV Columns", className="mb-0")),
            dbc.CardBody([
                html.P("Available columns from your uploaded file:"),
                html.Div([
                    dbc.Badge(col, color="light", text_color="dark", className="me-1 mb-1")
                    for col in columns
                ])
            ])
        ], className="mt-3")
    ]


def save_confirmed_device_mappings(confirm_clicks, floors, security, access, special, file_info):
    """Save confirmed device mappings to database"""
    if not confirm_clicks or not file_info:
        return no_update, no_update, no_update

    try:
        devices = file_info.get("devices", [])
        filename = file_info.get("filename", "")

        # Create user mappings from inputs
        user_mappings = {}
        for i, device in enumerate(devices):
            user_mappings[device] = {
                "floor_number": floors[i] if i < len(floors) else 1,
                "security_level": security[i] if i < len(security) else 5,
                "is_entry": "entry" in (access[i] if i < len(access) else []),
                "is_exit": "exit" in (access[i] if i < len(access) else []),
                "is_restricted": "is_restricted" in (special[i] if i < len(special) else []),  # ADD THIS
                "confidence": 1.0,
                "device_name": device,
                "source": "user_confirmed",
                "saved_at": datetime.now().isoformat(),
            }

        # Save to learning service database
        learning_service.save_user_device_mappings(filename, user_mappings)

        # Update global mappings
        from components.simple_device_mapping import _device_ai_mappings
        _device_ai_mappings.update(user_mappings)

        print(f"\u2705 Saved {len(user_mappings)} confirmed device mappings to database")

        success_alert = dbc.Toast(
            "✅ Device mappings saved to database!",
            header="Confirmed & Saved",
            is_open=True,
            dismissable=True,
            duration=3000,
        )

        return success_alert, False, False

    except Exception as e:
        print(f"\u274c Error saving device mappings: {e}")
        error_alert = dbc.Toast(
            f"❌ Error saving mappings: {e}",
            header="Error",
            is_open=True,
            dismissable=True,
            duration=5000,
        )
        return error_alert, no_update, no_update


def register_callbacks(manager: UnifiedCallbackCoordinator) -> None:
    """Register page callbacks using the provided coordinator."""

    manager.register_callback(
        Output("upload-data", "style"),
        Input("upload-more-btn", "n_clicks"),
        prevent_initial_call=True,
        callback_id="highlight_upload_area",
        component_name="file_upload",
    )(highlight_upload_area)

    manager.register_callback(
        [
            Output("upload-results", "children"),
            Output("file-preview", "children"),
            Output("file-info-store", "data"),
            Output("upload-nav", "children"),
            Output("current-file-info-store", "data"),
            Output("column-verification-modal", "is_open"),
            Output("device-verification-modal", "is_open"),
        ],
        [
            Input("upload-data", "contents"),
            Input("verify-columns-btn-simple", "n_clicks"),
            Input("classify-devices-btn", "n_clicks"),
            Input("column-verify-confirm", "n_clicks"),
            Input("column-verify-cancel", "n_clicks"),
            Input("device-verify-cancel", "n_clicks"),
            Input("device-verify-confirm", "n_clicks"),
            Input("url", "pathname"),
        ],
        [
            State("upload-data", "filename"),
            State({"type": "field-mapping", "column": ALL}, "value"),
            State({"type": "field-mapping", "column": ALL}, "id"),
            State("current-file-info-store", "data"),
            State("column-verification-modal", "is_open"),
            State("device-verification-modal", "is_open"),
        ],
        prevent_initial_call=False,
        callback_id="consolidated_upload_callback",
        component_name="file_upload",
    )(consolidated_upload_callback)

    manager.register_callback(
        [Output({"type": "column-mapping", "index": ALL}, "value")],
        [Input("column-verify-ai-auto", "n_clicks")],
        [State("current-file-info-store", "data")],
        prevent_initial_call=True,
        callback_id="apply_ai_suggestions",
        component_name="file_upload",
    )(apply_ai_suggestions)

    manager.register_callback(
        Output("device-modal-body", "children"),
        Input("device-verification-modal", "is_open"),
        State("current-file-info-store", "data"),
        prevent_initial_call=True,
        callback_id="populate_device_modal_with_learning",
        component_name="file_upload",
    )(populate_device_modal_with_learning)

    manager.register_callback(
        Output("modal-body", "children"),
        [Input("column-verification-modal", "is_open"), Input("current-file-info-store", "data")],
        prevent_initial_call=True,
        callback_id="populate_modal_content",
        component_name="file_upload",
    )(populate_modal_content)

    manager.register_callback(
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
        prevent_initial_call=True,
        callback_id="save_confirmed_device_mappings",
        component_name="file_upload",
    )(save_confirmed_device_mappings)


# Export functions for integration with other modules
__all__ = [
    "layout",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "process_uploaded_file",
    "save_ai_training_data",
    "register_callbacks",
]

print(f"\U0001f50d FILE_UPLOAD.PY LOADED - Callbacks should be registered")
