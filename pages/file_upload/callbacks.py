"""Callbacks for the file upload page."""
import logging
from typing import Any, Dict, List, Tuple

import pandas as pd
from dash import html, no_update
from dash._callback_context import callback_context
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc

from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from analytics.controllers import UnifiedAnalyticsController
from services.upload_service import process_uploaded_file
from services.device_learning_service import get_device_learning_service
from services.ai_suggestions import generate_column_suggestions

from .upload_handling import (
    build_success_alert,
    build_failure_alert,
    build_file_preview_component,
    get_uploaded_data,
    clear_uploaded_data,
    get_file_info,
)
from .ai_device_classification import (
    analyze_device_name_with_ai,
    auto_apply_learned_mappings,
)
from .modal_dialogs import handle_modal_dialogs, apply_ai_suggestions

from utils.upload_store import uploaded_data_store as _uploaded_data_store

logger = logging.getLogger(__name__)


def get_trigger_id() -> str:
    ctx = callback_context
    return ctx.triggered[0]["prop_id"] if ctx.triggered else ""


class Callbacks:
    """Container object for upload page callbacks."""

    def highlight_upload_area(self, n_clicks):
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
        upload_nav = html.Div([
            html.Hr(),
            html.H5("Ready to analyze?"),
            dbc.Button("🚀 Go to Analytics", href="/analytics", color="success", size="lg"),
        ])
        return (
            upload_results,
            file_preview_components,
            {},
            upload_nav,
            current_file_info,
            False,
            False,
        )

    def process_uploaded_files(self, contents_list: List[str] | str, filenames_list: List[str] | str) -> Tuple[Any, Any, Any, Any, Any, Any, Any]:
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
        clear_uploaded_data()
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
            content = parts[0] if len(parts) == 1 else f"{parts[0].split(',')[0]},{''.join(p.split(',')[1] for p in parts)}"
            try:
                result = process_uploaded_file(content, filename)
                if result["success"]:
                    df = result["data"]
                    rows = len(df)
                    cols = len(df.columns)
                    _uploaded_data_store.add_file(filename, df)
                    upload_results.append(build_success_alert(filename, rows, cols))
                    file_preview_components.append(build_file_preview_component(df, filename))
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
                        user_mappings = learning_service.get_user_device_mappings(filename)
                        if user_mappings:
                            from services.ai_mapping_store import ai_mapping_store
                            ai_mapping_store.clear()
                            for device, mapping in user_mappings.items():
                                mapping["source"] = "user_confirmed"
                                ai_mapping_store.set(device, mapping)
                        else:
                            from services.ai_mapping_store import ai_mapping_store
                            ai_mapping_store.clear()
                            auto_apply_learned_mappings(df, filename)
                    except Exception as e:  # pragma: no cover - best effort
                        logger.info(f"⚠️ Error: {e}")
                else:
                    upload_results.append(build_failure_alert(result["error"]))
            except Exception as e:  # pragma: no cover - best effort
                upload_results.append(build_failure_alert(f"Error processing {filename}: {str(e)}"))
        upload_nav = []
        if file_info_dict:
            upload_nav = html.Div([
                html.Hr(),
                html.H5("Ready to analyze?"),
                dbc.Button("🚀 Go to Analytics", href="/analytics", color="success", size="lg"),
            ])
        return (
            upload_results,
            file_preview_components,
            file_info_dict,
            upload_nav,
            current_file_info,
            no_update,
            no_update,
        )

    def handle_modal_dialogs(self, verify_clicks: int | None, classify_clicks: int | None, confirm_clicks: int | None, cancel_col_clicks: int | None, cancel_dev_clicks: int | None) -> Tuple[Any, Any, Any]:
        trigger_id = get_trigger_id()
        return handle_modal_dialogs(trigger_id, verify_clicks, classify_clicks, confirm_clicks, cancel_col_clicks, cancel_dev_clicks)

    def apply_ai_suggestions(self, n_clicks, file_info):
        return apply_ai_suggestions(n_clicks, file_info)


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
    ]
    for func, outputs, inputs, states, cid, extra in callback_defs:
        manager.register_callback(outputs, inputs, states, callback_id=cid, component_name="file_upload", **extra)(func)
    if controller is not None:
        controller.register_callback(
            "on_analysis_error",
            lambda aid, err: logger.error("File upload error: %s", err),
        )

__all__ = ["Callbacks", "get_trigger_id", "register_callbacks"]
