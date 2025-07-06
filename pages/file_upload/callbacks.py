import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

import dash_bootstrap_components as dbc
from dash import html, no_update
from analytics.controllers import UnifiedAnalyticsController
from core.callback_registry import debounce
from core.dash_profile import profile_callback
from dash.dependencies import ALL, Input, Output, State

from components.column_verification import save_verified_mappings
from config.dynamic_config import dynamic_config
from services.device_learning_service import get_device_learning_service
from services.task_queue import clear_task, create_task, get_status
from services.upload import AISuggestionService, ModalService, UploadProcessingService, get_trigger_id, save_ai_training_data
from services.upload.validators import ClientSideValidator
from utils.upload_store import uploaded_data_store as _uploaded_data_store
from . import _get_max_display_rows

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
        return task_id

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


def register_upload_callbacks(
    manager: "TrulyUnifiedCallbacks",
    controller: UnifiedAnalyticsController | None = None,
) -> None:
    cb = Callbacks()
    upload_ctrl = UnifiedUploadController(cb)

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

    for defs in (
        upload_ctrl.upload_callbacks(),
        upload_ctrl.progress_callbacks(),
        upload_ctrl.validation_callbacks(),
    ):
        _register(defs)

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


def register_callbacks(
    manager: "TrulyUnifiedCallbacks",
    controller: UnifiedAnalyticsController | None = None,
) -> None:
    """Alias for backward compatibility."""
    return register_upload_callbacks(manager, controller)
