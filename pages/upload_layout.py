"""Layout portion for the file upload page."""

import logging

import dash_bootstrap_components as dbc
from dash import dcc, html
from config.dynamic_config import dynamic_config

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
                                            dcc.Upload(
                                                id="upload-data",
                                                max_size=dynamic_config.get_max_upload_size_bytes(),  # Updated to use new method
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
                            )
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

__all__ = ["layout"]

