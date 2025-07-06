import logging
from typing import Any, List, Tuple

from dash.dependencies import ALL, Input, Output, State

from utils.upload_store import uploaded_data_store as _uploaded_data_store

from . import (
    AISuggestionService,
    ClientSideValidator,
    ModalService,
    UploadProcessingService,
)
from .managers import ChunkedUploadManager
from .upload_queue_manager import UploadQueueManager

logger = logging.getLogger(__name__)


class UnifiedUploadController:
    """Provide callback definitions for upload, progress and validation."""

    def __init__(self, callbacks: Any | None = None) -> None:
        self.cb = callbacks
        self.processing = UploadProcessingService(_uploaded_data_store)
        self.preview_processor = self.processing.async_processor
        self.ai = AISuggestionService()
        self.modal = ModalService()
        self.client_validator = ClientSideValidator()
        self.chunked = ChunkedUploadManager()
        self.queue = UploadQueueManager()

    # ------------------------------------------------------------------
    def upload_callbacks(self) -> List[Tuple[Any, Any, Any, Any, str, dict]]:
        return [
            (
                self.cb.highlight_upload_area,
                Output("drag-drop-upload", "className"),
                Input("upload-more-btn", "n_clicks"),
                None,
                "highlight_upload_area",
                {"prevent_initial_call": True},
            ),
            (
                self.cb.schedule_upload_task,
                Output("upload-task-id", "data", allow_duplicate=True),
                Input("drag-drop-upload", "contents"),
                State("drag-drop-upload", "filename"),
                "schedule_upload_task",
                {"prevent_initial_call": True, "allow_duplicate": True},
            ),
            (
                self.cb.display_client_validation,
                Output("upload-results", "children", allow_duplicate=True),
                Input("client-validation-store", "data"),
                None,
                "display_client_validation",
                {"prevent_initial_call": True, "allow_duplicate": True},
            ),
            (
                self.cb.reset_upload_progress,
                [
                    Output("upload-progress", "value", allow_duplicate=True),
                    Output("upload-progress", "label", allow_duplicate=True),
                    Output(
                        "upload-progress-interval", "disabled", allow_duplicate=True
                    ),
                ],
                Input("drag-drop-upload", "contents"),
                None,
                "reset_upload_progress",
                {"prevent_initial_call": True, "allow_duplicate": True},
            ),
            (
                self.cb.restore_upload_state,
                [
                    Output("upload-results", "children", allow_duplicate=True),
                    Output("file-preview", "children", allow_duplicate=True),
                    Output("file-info-store", "data", allow_duplicate=True),
                    Output("upload-nav", "children", allow_duplicate=True),
                    Output("current-file-info-store", "data", allow_duplicate=True),
                    Output(
                        "column-verification-modal", "is_open", allow_duplicate=True
                    ),
                    Output(
                        "device-verification-modal", "is_open", allow_duplicate=True
                    ),
                ],
                Input("url", "pathname"),
                None,
                "restore_upload_state",
                {"prevent_initial_call": "initial_duplicate", "allow_duplicate": True},
            ),
        ]

    # ------------------------------------------------------------------
    def progress_callbacks(self) -> List[Tuple[Any, Any, Any, Any, str, dict]]:
        return [
            (
                self.cb.update_progress_bar,
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
                self.cb.finalize_upload_results,
                [
                    Output("upload-results", "children", allow_duplicate=True),
                    Output("file-preview", "children", allow_duplicate=True),
                    Output("file-info-store", "data", allow_duplicate=True),
                    Output("upload-nav", "children", allow_duplicate=True),
                    Output("current-file-info-store", "data", allow_duplicate=True),
                    Output(
                        "column-verification-modal", "is_open", allow_duplicate=True
                    ),
                    Output(
                        "device-verification-modal", "is_open", allow_duplicate=True
                    ),
                    Output(
                        "upload-progress-interval", "disabled", allow_duplicate=True
                    ),
                ],
                Input("progress-done-trigger", "n_clicks"),
                State("upload-task-id", "data"),
                "finalize_upload_results",
                {"prevent_initial_call": True, "allow_duplicate": True},
            ),
        ]

    # ------------------------------------------------------------------
    def validation_callbacks(self) -> List[Tuple[Any, Any, Any, Any, str, dict]]:
        return [
            (
                self.cb.handle_modal_dialogs,
                [
                    Output("toast-container", "children", allow_duplicate=True),
                    Output(
                        "column-verification-modal", "is_open", allow_duplicate=True
                    ),
                    Output(
                        "device-verification-modal", "is_open", allow_duplicate=True
                    ),
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
                self.cb.apply_ai_suggestions,
                [Output({"type": "column-mapping", "index": ALL}, "value")],
                [Input("column-verify-ai-auto", "n_clicks")],
                [State("current-file-info-store", "data")],
                "apply_ai_suggestions",
                {"prevent_initial_call": True},
            ),
            (
                self.cb.populate_device_modal_with_learning,
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
                self.cb.populate_modal_content,
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
                self.cb.save_confirmed_device_mappings,
                [
                    Output("toast-container", "children", allow_duplicate=True),
                    Output(
                        "column-verification-modal", "is_open", allow_duplicate=True
                    ),
                    Output(
                        "device-verification-modal", "is_open", allow_duplicate=True
                    ),
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
                self.cb.save_verified_column_mappings,
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


__all__ = ["UnifiedUploadController"]
