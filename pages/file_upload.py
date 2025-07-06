#!/usr/bin/env python3
"""
Complete File Upload Page - Missing piece for consolidation
Integrates with analytics system
"""
import logging
from datetime import datetime
import time

import pandas as pd
from typing import Dict, Any, List, Tuple
from dash import html, dcc
from dash.dash import no_update
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from analytics.controllers import UnifiedAnalyticsController
from core.dash_profile import profile_callback
from core.callback_registry import debounce
from config.config import get_analytics_config

def _get_max_display_rows() -> int:
    return get_analytics_config().max_display_rows or 10000
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
from services.device_learning_service import get_device_learning_service
from utils.upload_store import uploaded_data_store as _uploaded_data_store
from services.upload_data_service import (
    get_uploaded_data as service_get_uploaded_data,
    get_uploaded_filenames as service_get_uploaded_filenames,
    clear_uploaded_data as service_clear_uploaded_data,
    get_file_info as service_get_file_info,
)
from config.dynamic_config import dynamic_config

from components.column_verification import save_verified_mappings
from services.upload import (
    UploadProcessingService,
    AISuggestionService,
    ModalService,
    get_trigger_id,
    save_ai_training_data,
)
from components.upload import ClientSideValidator

from services.task_queue import create_task, get_status, clear_task


logger = logging.getLogger(__name__)


def layout():
    """File upload page layout with persistent storage"""
    return dbc.Container(
        [
            # Removed redundant page header
            # Upload area
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [html.H5("Upload Data Files", className="mb-0")]
                                    ),
                                    dbc.CardBody(
                                        [
                                            DragDropUploadArea(
                                                id="upload-data",
                                                max_size=dynamic_config.get_max_upload_size_bytes(),  # Updated to use new method
                                                **{
                                                    "data-max-size": dynamic_config.get_max_upload_size_bytes()
                                                },
                                                children=html.Div(
                                                    [
                                                        html.Span(
                                                            [
                                                                html.I(
                                                                    className="fas fa-cloud-upload-alt fa-4x mb-3 text-primary",
                                                                    **{
                                                                        "aria-hidden": "true"
                                                                    },
                                                                ),
                                                                html.Span(
                                                                    "Upload icon",
                                                                    className="sr-only",
                                                                ),
                                                            ]
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
                                                className="file-upload-area",
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
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Progress(
                                id="upload-progress",
                                value=0,
                                label="0%",
                                striped=True,
                                animated=True,
                                **{"aria-label": "Overall upload progress"},
                            ),
                            html.Ul(id="file-progress-list", className="list-unstyled mt-2")
                        ]
                    )
                ],
                className="mb-3",
            ),
            # Hidden button triggered by SSE when upload completes
            dbc.Button("", id="progress-done-trigger", className="hidden"),
            html.Div(id="sse-trigger", style={"display": "none"}),
            # Data preview area
            dbc.Row([dbc.Col([html.Div(id="file-preview")])]),
            # Navigation to analytics
            dbc.Row([dbc.Col([html.Div(id="upload-nav")])]),
            # Container for toast notifications
            html.Div(id="toast-container"),
            # CRITICAL: Hidden placeholder buttons (using `.hidden` utility) to prevent callback errors
            html.Div(
                [
                    dbc.Button("", id="verify-columns-btn-simple", className="hidden"),
                    dbc.Button("", id="classify-devices-btn", className="hidden"),
                ],
                className="hidden",
            ),
            # Store for uploaded data info
            dcc.Store(id="file-info-store", data={}),
            dcc.Store(id="current-file-info-store"),
            dcc.Store(id="current-session-id", data="session_123"),
            dcc.Store(id="upload-task-id"),
            dcc.Store(id="client-validation-store", data=[]),
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
    return service_get_uploaded_data()


def get_uploaded_filenames() -> List[str]:
    """Get list of uploaded filenames."""
    return service_get_uploaded_filenames()


def clear_uploaded_data():
    """Clear all uploaded data."""
    service_clear_uploaded_data()


def get_file_info() -> Dict[str, Dict[str, Any]]:
    """Get information about uploaded files."""
    return service_get_file_info()


def check_upload_system_health() -> Dict[str, Any]:
    """Monitor upload system health."""
    issues = []
    storage_dir = _uploaded_data_store.storage_dir

    if not storage_dir.exists():
        issues.append(f"Storage directory missing: {storage_dir}")

    try:
        test_file = storage_dir / "test.tmp"
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:
        issues.append(f"Cannot write to storage directory: {e}")

    pending = len(_uploaded_data_store._save_futures)
    if pending > 10:
        issues.append(f"Too many pending saves: {pending}")

    return {"healthy": len(issues) == 0, "issues": issues}


class Callbacks:
    """Container object for upload page callbacks."""

    def __init__(self):
        self.processing = UploadProcessingService(_uploaded_data_store)
        self.preview_processor = self.processing.async_processor
        self.ai = AISuggestionService()
        self.modal = ModalService()
        self.client_validator = ClientSideValidator()


    def highlight_upload_area(self, n_clicks):
        """Highlight upload area when 'upload more' is clicked."""
        if n_clicks:
            return "file-upload-area file-upload-area--highlight"
        return "file-upload-area"

    def display_client_validation(self, data):
        """Show validation errors generated in the browser."""
        if not data:
            return no_update
        alerts = self.client_validator.build_error_alerts(data)
        return alerts

    async def restore_upload_state(self, pathname: str):
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

        file_infos = _uploaded_data_store.get_file_info()

        for filename, info in file_infos.items():
            path = info.get("path") or str(_uploaded_data_store.get_file_path(filename))
            try:
                df_preview = await self.preview_processor.preview_from_parquet(
                    path, rows=_get_max_display_rows()
                )
            except Exception:
                df_preview = _uploaded_data_store.load_dataframe(filename).head(_get_max_display_rows())
            rows = info.get("rows", len(df_preview))
            cols = info.get("columns", len(df_preview.columns))

            upload_results.append(
                self.processing.build_success_alert(
                    filename,
                    rows,
                    cols,
                    prefix="Previously uploaded:",
                    processed=False,
                )
            )

            file_preview_components.append(
                self.processing.build_file_preview_component(df_preview, filename)
            )

            current_file_info = {
                "filename": filename,
                "rows": rows,
                "columns": cols,
                "path": path,
                "ai_suggestions": info.get("ai_suggestions", {}),
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

    async def process_uploaded_files(
        self, contents_list: List[str] | str, filenames_list: List[str] | str
    ) -> Tuple[Any, Any, Any, Any, Any, Any, Any]:
        if not contents_list:
            return (
                [],
                [],
                {},
                [],
                {},
                no_update,
                no_update,
            )

        if not isinstance(contents_list, list):
            contents_list = [contents_list]
            filenames_list = [filenames_list]

        valid_contents: list[str] = []
        valid_filenames: list[str] = []
        alerts: list[Any] = []
        for content, fname in zip(contents_list, filenames_list):
            ok, msg = self.validator.validate(fname, content)
            if not ok:
                alerts.append(self.processing.build_failure_alert(msg))
            else:
                valid_contents.append(content)
                valid_filenames.append(fname)
                self.chunked.start_file(fname)
                self.queue.add_file(fname)

        if not valid_contents:
            return alerts, [], {}, [], {}, no_update, no_update

        result = await self.processing.process_files(valid_contents, valid_filenames)

        for fname in valid_filenames:
            self.chunked.finish_file(fname)
            self.queue.mark_complete(fname)

        result = list(result)
        result[0] = alerts + result[0]
        return tuple(result)

    def schedule_upload_task(
        self, contents_list: List[str] | str, filenames_list: List[str] | str
    ) -> str:
        """Schedule background processing of uploaded files."""
        if not contents_list:
            return ""

        if not isinstance(contents_list, list):
            contents_list = [contents_list]
        if not isinstance(filenames_list, list):
            filenames_list = [filenames_list]

        async_coro = self.processing.process_files(contents_list, filenames_list)
        task_id = create_task(async_coro)

    def reset_upload_progress(
        self, contents_list: List[str] | str
    ) -> Tuple[int, str, bool]:
        """Reset progress indicators when a new upload starts."""
        if not contents_list:
            return 0, "0%", True
        return 0, "0%", False

    def update_progress_bar(self, _n: int, task_id: str) -> Tuple[int, str, Any]:
        """Update the progress bar and per-file indicators."""

        status = get_status(task_id)
        progress = int(status.get("progress", 0))
        file_items = [
            html.Li(
                dbc.Progress(
                    value=self.chunked.get_progress(fname),
                    label=f"{fname} {self.chunked.get_progress(fname)}%",
                    striped=True,
                    animated=True,
                    id={"type": "file-progress", "name": fname},
                    **{"aria-label": f"Upload progress for {fname}"},
                )
            )
            for fname in self.queue.files
        ]
        return progress, f"{progress}%", file_items

    def finalize_upload_results(
        self, _n: int, task_id: str
    ) -> Tuple[Any, Any, Any, Any, Any, Any, Any, bool]:
        """Emit upload results once processing completes."""
        status = get_status(task_id)
        result = status.get("result")

        if status.get("done") and result is not None:
            clear_task(task_id)
            if isinstance(result, Exception):
                result = (
                    [self.processing.build_failure_alert(str(result))],
                    [],
                    {},
                    [],
                    {},
                    no_update,
                    no_update,
                )
            return (*result, True)

        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
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
        trigger_id = get_trigger_id()
        return self.modal.handle_dialogs(
            verify_clicks,
            classify_clicks,
            confirm_clicks,
            cancel_col_clicks,
            cancel_dev_clicks,
            trigger_id,
        )

    def apply_ai_suggestions(self, n_clicks, file_info):
        return self.ai.apply_ai_suggestions(n_clicks, file_info)

    def populate_device_modal_with_learning(self, is_open, file_info):
        """Populate the device modal with learned or AI-suggested data."""
        if not is_open:
            return "Modal closed", file_info

        logger.info("🔧 Populating device modal...")

        try:
            # First try to get devices from global store (saved mappings)
            from services.ai_mapping_store import ai_mapping_store

            store_devices = ai_mapping_store.all()

            if store_devices:
                logger.info(
                    f"📋 Found {len(store_devices)} saved devices - using SAVED mappings!"
                )

                # Create editable rows using saved mappings
                table_rows = []
                for i, (device_name, mapping) in enumerate(store_devices.items()):
                    floor = mapping.get("floor_number", 1)
                    security = mapping.get("security_level", 5)
                    is_entry = mapping.get("is_entry", False)
                    is_exit = mapping.get("is_exit", False)
                    is_elevator = mapping.get("is_elevator", False)
                    is_stairwell = mapping.get("is_stairwell", False)
                    is_fire_escape = mapping.get("is_fire_escape", False)
                    is_restricted = mapping.get("is_restricted", False)

                    # Create the same interactive row structure as original
                    row = html.Tr(
                        [
                            html.Td(html.Strong(device_name)),
                            html.Td(
                                [
                                    dbc.Input(
                                        id={"type": "device-floor", "index": i},
                                        type="number",
                                        value=floor,  # Pre-populate with saved value
                                        min=0,
                                        max=50,
                                        size="sm",
                                    )
                                ]
                            ),
                            html.Td(
                                [
                                    dbc.Checklist(
                                        id={"type": "device-access", "index": i},
                                        options=[
                                            {"label": "Entry", "value": "entry"},
                                            {"label": "Exit", "value": "exit"},
                                        ],
                                        value=[
                                            "entry" if is_entry else "",
                                            "exit" if is_exit else "",
                                        ],
                                        inline=True,
                                    )
                                ]
                            ),
                            html.Td(
                                [
                                    dbc.Checklist(
                                        id={"type": "device-special", "index": i},
                                        options=[
                                            {
                                                "label": "Elevator",
                                                "value": "is_elevator",
                                            },
                                            {
                                                "label": "Stairwell",
                                                "value": "is_stairwell",
                                            },
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
                                            "is_elevator" if is_elevator else "",
                                            "is_stairwell" if is_stairwell else "",
                                            "is_fire_escape" if is_fire_escape else "",
                                            "is_restricted" if is_restricted else "",
                                        ],
                                        inline=True,
                                    )
                                ]
                            ),
                            html.Td(
                                [
                                    dbc.Input(
                                        id={"type": "device-security", "index": i},
                                        type="number",
                                        value=security,  # Pre-populate with saved value
                                        min=0,
                                        max=10,
                                        size="sm",
                                    )
                                ]
                            ),
                        ]
                    )
                    table_rows.append(row)

                # Store device list for callback
                file_info["devices"] = list(store_devices.keys())

                return (
                    html.Div(
                        [
                            dbc.Alert(
                                [
                                    html.Strong("📋 SAVED MAPPINGS LOADED! "),
                                    f"Pre-filled {len(store_devices)} devices with your confirmed settings. You can edit and re-save.",
                                ],
                                color="success",
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
                                                    html.Th("Access"),
                                                    html.Th("Special"),
                                                    html.Th("Security (0-10)"),
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

            # Fallback: Generate AI analysis if no saved mappings (original logic)
            uploaded_data = get_uploaded_data()
            if not uploaded_data:
                return dbc.Alert("No uploaded data found", color="warning"), file_info

            all_devices = set()
            device_columns = [
                "door_id",
                "device_name",
                "DeviceName",
                "location",
                "door",
                "device",
            ]

            from services.ai_mapping_store import ai_mapping_store

            for filename, df in uploaded_data.items():
                logger.info(f"📄 Processing {filename} with {len(df)} rows")
                for col in df.columns:
                    col_lower = col.lower().strip()
                    if any(
                        device_col.lower() in col_lower for device_col in device_columns
                    ):
                        unique_vals = df[col].dropna().unique()
                        all_devices.update(str(val) for val in unique_vals)
                        logger.info(
                            f"   Found {len(unique_vals)} devices in column '{col}'"
                        )
                        # Pre-cache AI analyses for new devices
                        for device in unique_vals:
                            if not ai_mapping_store.get(device):
                                ai_analysis = self.ai.analyze_device_name_with_ai(
                                    device
                                )
                                ai_mapping_store.set(device, ai_analysis)
                                logger.info(
                                    f"   🚪 '{device}' → Floor: {ai_analysis.get('floor_number', 1)}, Security: {ai_analysis.get('security_level', 5)}"
                                )
                        break

            # Generate AI-populated interactive rows
            table_rows = []
            device_list = sorted(list(all_devices))
            file_info["devices"] = device_list

            cached_mappings = ai_mapping_store.all()
            for device_name in device_list:
                if device_name not in cached_mappings:
                    ai_mapping_store.set(
                        device_name, self.ai.analyze_device_name_with_ai(device_name)
                    )
            cached_mappings = ai_mapping_store.all()

            for i, device_name in enumerate(device_list):
                ai_analysis = cached_mappings.get(device_name, {})
                is_elevator_ai = ai_analysis.get("is_elevator", False)
                is_stairwell_ai = ai_analysis.get("is_stairwell", False)
                is_fire_escape_ai = ai_analysis.get("is_fire_escape", False)
                is_restricted_ai = ai_analysis.get("is_restricted", False)

                row = html.Tr(
                    [
                        html.Td(html.Strong(device_name)),
                        html.Td(
                            [
                                dbc.Input(
                                    id={"type": "device-floor", "index": i},
                                    type="number",
                                    value=ai_analysis.get("floor_number", 1),
                                    min=0,
                                    max=50,
                                    size="sm",
                                )
                            ]
                        ),
                        html.Td(
                            [
                                dbc.Checklist(
                                    id={"type": "device-access", "index": i},
                                    options=[
                                        {"label": "Entry", "value": "entry"},
                                        {"label": "Exit", "value": "exit"},
                                    ],
                                    value=[
                                        "entry" if ai_analysis.get("is_entry") else "",
                                        "exit" if ai_analysis.get("is_exit") else "",
                                    ],
                                    inline=True,
                                )
                            ]
                        ),
                        html.Td(
                            [
                                dbc.Checklist(
                                    id={"type": "device-special", "index": i},
                                    options=[
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
                                        "is_elevator" if is_elevator_ai else "",
                                        "is_stairwell" if is_stairwell_ai else "",
                                        "is_fire_escape" if is_fire_escape_ai else "",
                                        "is_restricted" if is_restricted_ai else "",
                                    ],
                                    inline=True,
                                )
                            ]
                        ),
                        html.Td(
                            [
                                dbc.Input(
                                    id={"type": "device-security", "index": i},
                                    type="number",
                                    value=ai_analysis.get("security_level", 5),
                                    min=0,
                                    max=10,
                                    size="sm",
                                )
                            ]
                        ),
                    ]
                )
                table_rows.append(row)

            return (
                html.Div(
                    [
                        dbc.Alert(
                            [
                                html.Strong("🤖 AI Analysis: "),
                                f"Generated mappings for {len(device_list)} devices. ",
                                "Check console for detailed AI debug info.",
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
                                                html.Th("Access"),
                                                html.Th("Special"),
                                                html.Th("Security (0-10)"),
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

        except Exception as e:
            logger.error(f"❌ Error in device modal: {e}")
            return dbc.Alert(f"Error: {e}", color="danger"), file_info

    async def populate_modal_content(self, is_open, file_info):
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
        columns = file_info.get("columns", [])
        if not columns:
            path = file_info.get("path") or str(
                _uploaded_data_store.get_file_path(filename)
            )
            try:
                df_tmp = await self.preview_processor.preview_from_parquet(path, rows=0)
                columns = df_tmp.columns.tolist()
            except Exception:
                df_tmp = _uploaded_data_store.load_dataframe(filename)
                columns = df_tmp.columns.tolist()
        ai_suggestions = file_info.get("ai_suggestions", {})

        # ADD THIS BLOCK HERE - Check for saved column mappings
        try:
            df = _uploaded_data_store.load_dataframe(filename)
            if df is not None:
                from services.consolidated_learning_service import get_learning_service

                learned = get_learning_service().get_learned_mappings(df, filename)
                saved_column_mappings = learned.get("column_mappings", {})

                if saved_column_mappings:
                    logger.info(
                        f"📋 Found {len(saved_column_mappings)} saved column mappings for {filename}"
                    )

                    # Inject saved mappings as high-confidence AI suggestions
                    for standard_field, csv_column in saved_column_mappings.items():
                        ai_suggestions[csv_column] = {
                            "field": standard_field,
                            "confidence": 1.0,
                            "source": "saved",
                        }
                    logger.info(
                        f"📋 Pre-filled saved mappings: {saved_column_mappings}"
                    )
        except Exception as e:
            logger.debug(f"No saved mappings: {e}")
        # END OF ADDITION

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
                            className="csv-mapping-field-col",
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
                                    className="csv-mapping-dropdown",
                                )
                            ],
                            className="csv-mapping-column-col",
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
                            className="csv-mapping-ai-col",
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
                                        className="csv-mapping-field-col",
                                    ),
                                    html.Th(
                                        "Maps to CSV Column (Variable)",
                                        className="csv-mapping-column-col",
                                    ),
                                    html.Th(
                                        "AI Confidence",
                                        className="csv-mapping-ai-col",
                                    ),
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

            if not filename:
                raise ValueError("No filename provided in file_info")

            if not devices:
                raise ValueError("No devices found in file_info")

            df = None
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    logger.info(
                        f"🔄 Attempt {attempt + 1}/{max_attempts} to load file: {filename}"
                    )
                    _uploaded_data_store.wait_for_pending_saves()
                    available_files = _uploaded_data_store.get_filenames()
                    logger.info(f"📁 Available files: {available_files}")
                    if filename not in available_files:
                        raise ValueError(
                            f"File '{filename}' not found in upload store. Available: {available_files}"
                        )
                    df = _uploaded_data_store.load_dataframe(filename)
                    if df is None:
                        raise ValueError(
                            f"Failed to load DataFrame for '{filename}' - returned None"
                        )
                    if df.empty:
                        raise ValueError(f"DataFrame for '{filename}' is empty")
                    logger.info(
                        f"✅ Successfully loaded file: {filename} ({len(df)} rows, {len(df.columns)} columns)"
                    )
                    break
                except Exception as load_error:
                    logger.warning(f"⚠️ Attempt {attempt + 1} failed: {load_error}")
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"❌ All {max_attempts} attempts failed to load '{filename}'"
                        )
                        storage_dir = _uploaded_data_store.storage_dir
                        logger.error(f"📁 Storage directory: {storage_dir}")
                        logger.error(
                            f"📁 Storage directory exists: {storage_dir.exists()}"
                        )
                        if storage_dir.exists():
                            disk_files = list(storage_dir.glob("*.parquet"))
                            logger.error(
                                f"📁 Disk files: {[f.name for f in disk_files]}"
                            )
                        raise ValueError(
                            f"Cannot load uploaded file after {max_attempts} attempts: {load_error}"
                        )
                    time.sleep(0.5)

            if df is None:
                raise ValueError(f"Data for '{filename}' could not be loaded")
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
            logger.error(f"❌ Error saving device mappings: {e}")

            error_msg = str(e)
            if "not found in upload store" in error_msg:
                error_msg += "\n\nTry refreshing the page and uploading the file again."
            elif "empty" in error_msg.lower():
                error_msg += "\n\nThe uploaded file appears to be empty."
            elif "load" in error_msg.lower():
                error_msg += "\n\nThere was an issue accessing the uploaded file."

            error_alert = dbc.Toast(
                f"❌ Error saving mappings: {error_msg}",
                header="Error",
                is_open=True,
                dismissable=True,
                duration=8000,
            )
            return error_alert, no_update, no_update

    def save_verified_column_mappings(
        self, confirm_clicks, values, ids, file_info
    ) -> Any:
        """Persist verified column mappings using learning service."""

        if not confirm_clicks or not file_info:
            return no_update
        # DEBUG: Log what we're saving
        logger.info(f"🔍 DEBUG save_verified_column_mappings called:")
        logger.info(f"🔍 DEBUG - confirm_clicks: {confirm_clicks}")
        logger.info(f"🔍 DEBUG - values: {values}")
        logger.info(f"🔍 DEBUG - ids: {ids}")
        logger.info(
            f"🔍 DEBUG - file_info filename: {file_info.get('filename', 'N/A')}"
        )

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

                df = _uploaded_data_store.load_dataframe(filename)
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


# ------------------------------------------------------------
# Callback manager for the upload page
# ------------------------------------------------------------


def register_callbacks(
    manager: "TrulyUnifiedCallbacks",
    controller: UnifiedAnalyticsController | None = None,
) -> None:
    """Instantiate :class:`Callbacks` and register its methods."""

    cb = Callbacks()

    def _register(defs: List[tuple]):
        for func, outputs, inputs, states, cid, extra in defs:
            manager.unified_callback(
                outputs,
                inputs,
                states,
                callback_id=cid,
                component_name="file_upload",
                **extra,
            )(debounce()(profile_callback(cid)(func)))

    upload_callbacks = [
        (
            cb.highlight_upload_area,
            Output("upload-data", "className"),
            Input("upload-more-btn", "n_clicks"),
            None,
            "highlight_upload_area",
            {"prevent_initial_call": True},
        ),
        (
            cb.schedule_upload_task,
            Output("upload-task-id", "data", allow_duplicate=True),
            Input("upload-data", "contents"),
            State("upload-data", "filename"),
            "schedule_upload_task",
            {"prevent_initial_call": True, "allow_duplicate": True},
        ),
        (
            cb.display_client_validation,
            Output("upload-results", "children", allow_duplicate=True),
            Input("client-validation-store", "data"),
            None,
            "display_client_validation",
            {"prevent_initial_call": True, "allow_duplicate": True},
        ),
        (
            cb.reset_upload_progress,
            [
                Output("upload-progress", "value", allow_duplicate=True),
                Output("upload-progress", "label", allow_duplicate=True),
                Output("upload-progress-interval", "disabled", allow_duplicate=True),
            ],
            Input("upload-data", "contents"),
            None,
            "reset_upload_progress",
            {"prevent_initial_call": True, "allow_duplicate": True},
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
    ]

    progress_callbacks = [
        (
            cb.update_progress_bar,
            [
                Output("upload-progress", "value", allow_duplicate=True),
                Output("upload-progress", "label", allow_duplicate=True),
                Output("file-progress-list", "children", allow_duplicate=True),
            ],
            Input("upload-progress-interval", "n_intervals"),
            State("upload-task-id", "data"),
            "update_progress_bar",
            {"prevent_initial_call": True, "allow_duplicate": True},
        ),
        (
            cb.finalize_upload_results,
            [
                Output("upload-results", "children", allow_duplicate=True),
                Output("file-preview", "children", allow_duplicate=True),
                Output("file-info-store", "data", allow_duplicate=True),
                Output("upload-nav", "children", allow_duplicate=True),
                Output("current-file-info-store", "data", allow_duplicate=True),
                Output("column-verification-modal", "is_open", allow_duplicate=True),
                Output("device-verification-modal", "is_open", allow_duplicate=True),
                Output("upload-progress-interval", "disabled", allow_duplicate=True),
            ],
            Input("progress-done-trigger", "n_clicks"),
            State("upload-task-id", "data"),
            "finalize_upload_results",
            {"prevent_initial_call": True, "allow_duplicate": True},
        ),
    ]

    modal_callbacks = [
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

    _register(upload_callbacks)
    _register(progress_callbacks)
    _register(modal_callbacks)

    manager.app.clientside_callback(
        "function(tid){if(window.startUploadProgress){window.startUploadProgress(tid);} return '';}",
        Output("sse-trigger", "children"),
        Input("upload-task-id", "data"),
    )

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
    "check_upload_system_health",
    "save_ai_training_data",
    "register_callbacks",
]

logger.info(f"\U0001f50d FILE_UPLOAD.PY LOADED - Callbacks should be registered")
