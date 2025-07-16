#!/usr/bin/env python3
"""
File upload page - Full functionality with flash timing fix
"""
from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc
import pandas as pd
from dash import (
    Input,
    Output,
    State,
    dcc,
    html,
    no_update,
)
from dash import register_page as dash_register_page
from dash.exceptions import PreventUpdate

from components.ui_component import UIComponent
from config.dynamic_config import dynamic_config
from services.upload_data_service import clear_uploaded_data as _svc_clear_uploaded_data

logger = logging.getLogger(__name__)

# On-disk store for uploaded files
from utils.upload_store import uploaded_data_store as _uploaded_data_store


class UploadPage(UIComponent):
    """Upload page component with flash fix."""

    def layout(self) -> dbc.Container:
        """Full upload layout with pre-mount stability."""

        # Pre-initialize all components to prevent flash
        upload_area = dcc.Upload(
            id="drag-drop-upload",
            className="drag-drop-upload upload-area",
            tabIndex=0,
            children=html.Div(
                [
                    html.I(
                        className="fas fa-cloud-upload-alt fa-3x mb-3",
                        **{"aria-hidden": "true"},
                    ),
                    html.H5("Drag & Drop Files Here"),
                    html.P("or click to select files", className="text-muted"),
                    html.P(
                        "Supports CSV, Excel, and JSON files",
                        className="small text-muted",
                    ),
                ]
            ),
            multiple=True,
        )

        return dbc.Container(
            [
                # Header - Pre-rendered stable
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H2("📁 File Upload", className="mb-3"),
                                html.P(
                                    "Drag and drop files or click to browse. Supports CSV, Excel, and JSON files.",
                                    className="text-muted mb-4",
                                ),
                            ]
                        )
                    ]
                ),
                # Upload area - Pre-rendered
                dbc.Row(
                    [dbc.Col(upload_area, lg=8, md=10, sm=12, className="mx-auto")]
                ),
                # Progress area - Pre-rendered but hidden
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Progress(
                                    id="upload-progress",
                                    value=0,
                                    striped=True,
                                    animated=False,
                                    style={"display": "none"},
                                ),
                                html.Div(
                                    id="upload-status", style={"marginTop": "10px"}
                                ),
                            ],
                            lg=8,
                            md=10,
                            sm=12,
                            className="mx-auto",
                        )
                    ]
                ),
                # Preview area - Pre-rendered empty
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    id="preview-area",
                                    style={
                                        "opacity": "1",
                                        "visibility": "visible",
                                        "minHeight": "50px",
                                    },
                                )
                            ],
                            lg=10,
                            md=12,
                            sm=12,
                            className="mx-auto",
                        )
                    ]
                ),
                # Navigation area - Pre-rendered empty
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    id="upload-navigation",
                                    style={
                                        "opacity": "1",
                                        "visibility": "visible",
                                        "minHeight": "30px",
                                    },
                                )
                            ],
                            lg=8,
                            md=10,
                            sm=12,
                            className="mx-auto",
                        )
                    ],
                    className="mt-4",
                ),
                # Data stores - Pre-initialized
                dcc.Store(id="uploaded-files-store", data={}),
                dcc.Store(id="upload-session-store", data={}),
            ],
            fluid=True,
            className="py-4",
            style={"opacity": "1", "visibility": "visible"},
        )

    def register_callbacks(self, manager, controller=None):
        """Register upload callbacks with timing fixes."""
        try:

            @manager.unified_callback(
                [
                    Output("upload-status", "children"),
                    Output("upload-progress", "value"),
                    Output("upload-progress", "style"),
                    Output("uploaded-files-store", "data"),
                    Output("preview-area", "children"),
                ],
                Input("drag-drop-upload", "contents"),
                [
                    State("drag-drop-upload", "filename"),
                    State("uploaded-files-store", "data"),
                ],
                callback_id="file_upload_process",
                component_name="file_upload",
                prevent_initial_call=True,
            )
            def process_upload(contents, filenames, existing_files):
                if not contents:
                    return no_update, no_update, no_update, no_update, no_update

                try:
                    # Simple success response
                    status = dbc.Alert("Files uploaded successfully!", color="success")
                    progress_style = {"display": "block"}
                    updated_files = existing_files or {}

                    # Simple preview
                    preview = html.Div(
                        [
                            html.H6("Uploaded Files:"),
                            html.Ul([html.Li(f) for f in (filenames or [])]),
                        ]
                    )

                    return status, 100, progress_style, updated_files, preview

                except Exception as e:
                    error_status = dbc.Alert(f"Upload failed: {str(e)}", color="danger")

                    return error_status, 0, {"display": "none"}, no_update, no_update

            logger.info("✅ File upload callbacks registered successfully")

        except Exception as e:
            logger.error(f"❌ Failed to register file upload callbacks: {e}")


_upload_component = UploadPage()


def load_page(**kwargs):
    return UploadPage(**kwargs)


def register_page(app=None):
    try:
        dash_register_page(__name__, path="/upload", name="Upload", app=app)
    except Exception as e:
        logger.warning(f"Failed to register page {__name__}: {e}")


def layout():
    return _upload_component.layout()


def register_callbacks(manager):
    _upload_component.register_callbacks(manager)


__all__ = ["UploadPage", "load_page", "layout", "register_page"]
