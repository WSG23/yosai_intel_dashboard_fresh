"""Callback registration utilities for upload components."""

from __future__ import annotations

import logging
from typing import Any, List, Tuple

from dash import no_update
from dash.dependencies import ALL, Input, Output, State

from core.callback_registry import debounce
from core.dash_profile import profile_callback
from upload_core import UploadCore

logger = logging.getLogger(__name__)


class UploadCallbackManager:
    """Register Dash callbacks for the upload workflow."""

    def __init__(self, core: UploadCore | None = None) -> None:
        self.core = core or UploadCore()

    def register(self, manager, controller=None) -> None:
        cb = self.core

        def _reg(defs: List[Tuple]):
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
                Output("drag-drop-upload", "className"),
                Input("upload-more-btn", "n_clicks"),
                None,
                "highlight_upload_area",
                {"prevent_initial_call": True},
            ),
            (
                cb.schedule_upload_task,
                Output("upload-task-id", "data", allow_duplicate=True),
                Input("drag-drop-upload", "contents"),
                State("drag-drop-upload", "filename"),
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
                    Output(
                        "upload-progress-interval", "disabled", allow_duplicate=True
                    ),
                ],
                Input("drag-drop-upload", "contents"),
                None,
                "reset_upload_progress",
                {"prevent_initial_call": True, "allow_duplicate": True},
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

        _reg(upload_callbacks)
        _reg(progress_callbacks)

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


__all__ = ["UploadCallbackManager"]
