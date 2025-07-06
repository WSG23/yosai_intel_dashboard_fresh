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
from services.upload.unified_controller import UnifiedUploadController
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


class Callbacks(UploadCore):
    """Backward compatibility wrapper"""
    pass

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
    "register_upload_callbacks",
]

logger.info(f"\U0001f50d FILE_UPLOAD.PY LOADED - Callbacks should be registered")
