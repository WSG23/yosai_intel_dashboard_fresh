#!/usr/bin/env python3
"""
Stable file upload component with preserved backend integration.
Fixed: Import and drag/drop functionality.
"""

from __future__ import annotations

import logging
from typing import Any, List, Dict

import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate

# Fixed import - use existing UploadArea class
from components.upload.ui.upload_area import UploadArea
from services.upload.core.processor import UploadProcessingService
from services.data_processing.async_file_processor import AsyncFileProcessor
from services.upload.core.validator import ClientSideValidator
from utils.upload_store import UploadedDataStore
from core.unicode import safe_encode_text

logger = logging.getLogger(__name__)


class StableFileUploadComponent:
    """Stable upload component preserving all backend services."""

    def __init__(self) -> None:
        # Initialize all preserved backend services
        self.upload_store = UploadedDataStore()
        self.file_processor = AsyncFileProcessor()
        self.validator = ClientSideValidator()
        self.processing_service = UploadProcessingService(
            store=self.upload_store,
            processor=self.file_processor,
            validator=self.validator,
        )

        # Initialize upload area with proper handler
        self.upload_area = UploadArea(
            upload_handler=self._handle_upload,
            upload_id="drag-drop-upload",
        )

    def layout(self) -> html.Div:
        """Return the stable Dash layout for the upload page."""
        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            [
                                                html.H5(
                                                    "Upload Data Files",
                                                    className="mb-0",
                                                )
                                            ]
                                        ),
                                        dbc.CardBody(
                                            [
                                                # Use the UploadArea directly - it already creates dcc.Upload
                                                self.upload_area.render()
                                            ]
                                        ),
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                # Progress indicators (preserved from original)
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
                                )
                            ]
                        )
                    ],
                    className="mb-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Ul(
                                    id="file-progress-list", className="list-unstyled"
                                )
                            ]
                        )
                    ]
                ),
                # Hidden trigger for progress completion
                dbc.Button("", id="progress-done-trigger", className="visually-hidden"),
                # Preview and navigation (preserved from original)
                html.Div(id="preview-area"),
                dbc.Button(
                    "Next",
                    id="to-column-map-btn",
                    color="primary",
                    className="mt-2",
                    disabled=True,
                ),
                # Data stores (preserved from original)
                dcc.Store(id="uploaded-df-store"),
                dcc.Store(id="file-info-store", data={}),
                dcc.Store(id="current-file-info-store"),
                dcc.Store(id="current-session-id", data="session_123"),
                dcc.Store(id="upload-task-id"),
                dcc.Store(id="client-validation-store", data=[]),
                dcc.Interval(
                    id="upload-progress-interval", interval=1000, disabled=True
                ),
                # Modals (preserved from original)
                self._create_column_mapping_modal(),
                self._create_device_verification_modal(),
            ],
            fluid=True,
        )

    def _create_column_mapping_modal(self) -> dbc.Modal:
        """Create column mapping modal (preserved functionality)."""
        return dbc.Modal(
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
        )

    def _create_device_verification_modal(self) -> dbc.Modal:
        """Create device verification modal (preserved functionality)."""
        return dbc.Modal(
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
        )

    def _handle_upload(self, contents: List[str], filenames: List[str]) -> str:
        """Handle file upload with Unicode safety."""
        if not contents or not filenames:
            return "No files provided"

        safe_contents = [safe_encode_text(c) for c in contents]
        safe_filenames = [safe_encode_text(f) for f in filenames]

        try:
            return self.processing_service.process_files(safe_contents, safe_filenames)
        except Exception as e:
            logger.error(f"Upload processing failed: {e}")
            return f"Upload failed: {safe_encode_text(str(e))}"

    def register_consolidated_callbacks(self, manager: Any) -> None:
        """Register all callbacks in a consolidated manner."""

        # Main upload handler callback - listens to dcc.Upload contents
        @manager.register_callback(
            [
                Output("preview-area", "children"),
                Output("to-column-map-btn", "disabled"),
                Output("uploaded-df-store", "data"),
                Output("upload-progress-interval", "disabled"),
            ],
            Input("drag-drop-upload", "contents"),
            [State("drag-drop-upload", "filename")],
            prevent_initial_call=True,
            callback_id="file_upload_handle",
            component_name="stable_file_upload",
        )
        def handle_upload(contents, filenames):
            if not contents or not filenames:
                raise PreventUpdate

            # Delegate to the _handle_upload method
            task_id = self._handle_upload(contents, filenames)

            # Return: no immediate preview, enable Next button, store task_id, enable progress polling
            return [], False, {"task_id": task_id}, False

        # Progress update callback (unchanged)
        @manager.register_callback(
            [
                Output("upload-progress", "value"),
                Output("upload-progress", "label"),
                Output("file-progress-list", "children"),
                Output("progress-done-trigger", "disabled"),
            ],
            Input("upload-progress-interval", "n_intervals"),
            prevent_initial_call=True,
            callback_id="file_upload_progress",
            component_name="stable_file_upload",
        )
        def update_upload_progress(n_intervals):
            try:
                # Simulated progress logic (replace with your real tracker)
                progress = min(100, (n_intervals or 0) * 20)
                items = [
                    html.Li(f"Processing file {i + 1}...")
                    for i in range(progress // 20)
                ]
                done = progress >= 100
                return progress, f"{progress}%", items, done
            except Exception:
                return 0, "0%", [], True

        # Finalization callback (unchanged)
        @manager.register_callback(
            [
                Output("upload-progress-interval", "disabled", allow_duplicate=True),
                Output("upload-progress", "style", allow_duplicate=True),
                Output("preview-area", "style", allow_duplicate=True),
            ],
            Input("progress-done-trigger", "n_clicks"),
            prevent_initial_call=True,
            callback_id="file_upload_finalize",
            component_name="stable_file_upload",
        )
        def finalize_upload(n_clicks):
            if not n_clicks:
                raise PreventUpdate
            return True, {"display": "none"}, {"display": "block"}

    def validate_component_state(self, manager=None) -> bool:
        """Validate that all preserved services are properly initialized."""
        services = [
            "upload_store",
            "file_processor",
            "validator",
            "processing_service",
            "upload_area",
        ]
        return all(hasattr(self, s) and getattr(self, s) is not None for s in services)


def register_callbacks(manager: Any) -> None:
    """Module-level callback registration function expected by app.py."""
    try:
        # Create component instance and register its callbacks
        upload_component = StableFileUploadComponent()
        upload_component.register_consolidated_callbacks(manager)
        logger.info("✅ Upload callbacks registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register upload callbacks: {e}")
        # Don't fail completely - provide minimal fallback
        pass


def layout() -> html.Div:
    """Module-level layout function for compatibility."""
    try:
        upload_component = StableFileUploadComponent()
        return upload_component.layout()
    except Exception as e:
        logger.error(f"❌ Failed to create upload layout: {e}")
        # Fallback minimal layout
        return html.Div([html.H4("Upload Page"), html.P(f"Error: {str(e)}")])


__all__ = ["StableFileUploadComponent", "register_callbacks", "layout"]

def register_callbacks(manager: Any) -> None:
    """Module-level callback registration function expected by app.py."""
    try:
        upload_component = StableFileUploadComponent()
        upload_component.register_consolidated_callbacks(manager)
        logger.info("✅ Upload callbacks registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register upload callbacks: {e}")
        pass


def layout() -> html.Div:
    """Module-level layout function for compatibility."""
    try:
        upload_component = StableFileUploadComponent()
        return upload_component.layout()
    except Exception as e:
        logger.error(f"❌ Failed to create upload layout: {e}")
        return html.Div([html.H4("Upload Page"), html.P(f"Error: {str(e)}")])



def safe_upload_layout():
    """Unicode-safe wrapper for app_factory."""
    return layout()

__all__ = [
    "StableFileUploadComponent",
    "register_callbacks",
    "layout",
    "safe_upload_layout",
]

