from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html
from flask import session
import uuid

from components.device_verification import register_modal_callback
from components.upload import UploadArea
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from typing import Any


class FileUploadComponent:
    """Simple wrapper bundling the upload layout and callbacks."""

    def __init__(self) -> None:
        pass

    def layout(self) -> html.Div:
        """Return the Dash layout for the upload page."""
        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader([
                                        html.H5("Upload Data Files", className="mb-0")
                                    ]),
                                    dbc.CardBody([UploadArea().render()]),
                                ]
                            )
                        )
                    ]
                ),
                dbc.Row([dbc.Col(dbc.Progress(id="upload-progress", value=0, label="0%", striped=True, animated=True)),], className="mb-2"),
                dbc.Row([dbc.Col(html.Ul(id="file-progress-list", className="list-unstyled"))]),
                html.Div(id="preview-area"),
                dbc.Button("Next", id="to-column-map-btn", color="primary", className="mt-2", disabled=True),
                html.Div(id="uploaded-df-store"),
                html.Div(id="file-info-store"),
                html.Div(id="current-file-info-store"),
                html.Div(id="current-session-id"),
                html.Div(id="upload-task-id"),
                html.Div(id="client-validation-store"),
                dcc.Interval(id="upload-progress-interval", interval=1000, disabled=True),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Column Mapping")),
                        dbc.ModalBody(
                            "Configure column mappings here", id="modal-body"
                        ),
                        dbc.ModalFooter(
                            [
                                dbc.Button(
                                    "Cancel",
                                    id="column-verify-cancel",
                                    color="secondary",
                                ),
                                dbc.Button(
                                    "Confirm",
                                    id="column-verify-confirm",
                                    color="success",
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
                                    "Cancel",
                                    id="device-verify-cancel",
                                    color="secondary",
                                ),
                                dbc.Button(
                                    "Confirm",
                                    id="device-verify-confirm",
                                    color="success",
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

    def register_callbacks(
        self, manager: TrulyUnifiedCallbacks, controller: Any | None = None
    ) -> None:
        """Register upload callbacks with the given manager."""
        register_modal_callback(manager)
        manager.register_upload_callbacks(controller)


__all__ = ["FileUploadComponent"]
