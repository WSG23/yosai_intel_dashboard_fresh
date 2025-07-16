#!/usr/bin/env python3
"""Simplified file upload page compatible with basic routing."""
from __future__ import annotations

import base64
import logging
from io import BytesIO
from typing import List

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate

from utils.upload_store import uploaded_data_store

logger = logging.getLogger(__name__)


def layout() -> dbc.Container:
    """Return the upload page layout."""
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
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2("\ud83d\udcc1 File Upload", className="mb-3"),
                            html.P(
                                "Drag and drop files or click to browse. Supports CSV, "
                                "Excel, and JSON files.",
                                className="text-muted mb-4",
                            ),
                        ]
                    )
                ]
            ),
            dbc.Row([dbc.Col(upload_area, lg=8, md=10, sm=12, className="mx-auto")]),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(id="upload-status"),
                            html.Div(id="preview-area"),
                        ],
                        lg=10,
                        md=12,
                        sm=12,
                        className="mx-auto",
                    )
                ]
            ),
        ],
        fluid=True,
        className="py-4",
    )


@callback(
    Output("upload-status", "children"),
    Output("preview-area", "children"),
    Input("drag-drop-upload", "contents"),
    State("drag-drop-upload", "filename"),
    prevent_initial_call=True,
)
def handle_upload(contents: str | List[str], filenames: str | List[str]):
    """Handle uploaded files and store them using :mod:`upload_store`."""
    if not contents:
        raise PreventUpdate

    if not isinstance(contents, list):
        contents = [contents]
        filenames = [filenames]  # type: ignore[list-item]

    alerts = []
    previews = []

    for content, name in zip(contents, filenames):
        try:
            header, data = content.split(",", 1)
            decoded = base64.b64decode(data)
            buf = BytesIO(decoded)

            if name.lower().endswith(".csv"):
                df = pd.read_csv(buf)
            elif name.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(buf)
            elif name.lower().endswith(".json"):
                df = pd.read_json(buf)
            else:
                alerts.append(
                    dbc.Alert(f"Unsupported file type for {name}", color="warning")
                )
                continue

            uploaded_data_store.add_file(name, df)
            table = dbc.Table.from_dataframe(df.head(5), striped=True, bordered=True)
            previews.append(html.Div([html.H6(name), table], className="mb-4"))
            alerts.append(
                dbc.Alert(f"Uploaded {name}", color="success", dismissable=True)
            )
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Upload failed for %s: %s", name, exc)
            alerts.append(dbc.Alert(f"Failed to process {name}", color="danger"))

    return alerts, previews


def register_page():
    """Register this page with Dash Pages if available."""
    try:
        import dash

        if hasattr(dash, "_current_app") and dash._current_app is not None:
            dash.register_page(__name__, path="/upload", name="Upload")
        else:
            from dash import register_page as dash_register_page

            dash_register_page(__name__, path="/upload", name="Upload")
    except Exception as e:  # pragma: no cover - best effort
        logger.warning("Failed to register page %s: %s", __name__, e)


def register_callbacks(app):
    """Compatibility wrapper for app callback registration."""
    # callbacks are declared with the `@callback` decorator, so nothing to do.
    return app


__all__ = ["layout", "register_page", "register_callbacks"]
