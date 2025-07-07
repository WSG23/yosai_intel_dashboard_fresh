#!/usr/bin/env python3
"""Drag and drop file upload component with progress display."""
from __future__ import annotations

import base64
import io
import logging
from typing import Any

import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, html, no_update
from dash.dependencies import Input, Output, State

from core.unicode_processor import safe_unicode_encode

logger = logging.getLogger(__name__)


class FileUploadComponent:
    """Render a drag and drop upload interface."""

    def __init__(self, upload_id: str = "file-upload") -> None:
        self.upload_id = upload_id
        self.area_id = f"{upload_id}-area"
        self.progress_id = f"{upload_id}-progress"
        self.status_id = f"{upload_id}-status"

    # ------------------------------------------------------------------
    def render(self) -> html.Div:
        """Return the upload area with progress and status elements."""

        return html.Div(
            [
                dcc.Upload(
                    id=self.upload_id,
                    multiple=False,
                    className="drag-drop-upload__input",
                    children=html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-cloud-upload-alt fa-3x",
                                        **{"aria-hidden": "true"},
                                    ),
                                    html.Span("Upload icon", className="sr-only"),
                                ]
                            ),
                            html.P(
                                "Drag and drop files or click to select",
                                id=f"{self.upload_id}-label",
                                className="mb-1",
                            ),
                        ],
                        className="drag-drop-upload__inner",
                    ),
                ),
                dbc.Progress(
                    id=self.progress_id,
                    value=0,
                    label="0%",
                    striped=True,
                    animated=True,
                    className="mt-2",
                ),
                html.Div(id=self.status_id, className="mt-2"),
            ],
            id=self.area_id,
            className="drag-drop-upload drag-drop-upload--idle",
            tabIndex=0,
            role="button",
            **{"aria-describedby": f"{self.upload_id}-label"},
        )

    # ------------------------------------------------------------------
    def register_callbacks(self, app) -> None:
        """Register Dash callbacks for the component."""

        @app.callback(
            [
                Output(self.status_id, "children"),
                Output(self.progress_id, "value"),
                Output(self.progress_id, "label"),
                Output(self.area_id, "className"),
            ],
            Input(self.upload_id, "contents"),
            State(self.upload_id, "filename"),
            prevent_initial_call=True,
        )
        def _handle_upload(contents: str | list[str] | None, filename: str | list[str] | None):
            if not contents or not filename:
                return no_update, no_update, no_update, "drag-drop-upload drag-drop-upload--idle"

            if isinstance(contents, list):
                contents = contents[0]
                filename = filename[0] if isinstance(filename, list) else filename

            try:
                df = self._process_file(contents, str(filename))
                msg = (
                    f"Uploaded {safe_unicode_encode(filename)}: {len(df)} rows x {len(df.columns)} columns"
                )
                cls = "drag-drop-upload drag-drop-upload--success"
                return msg, 100, "100%", cls
            except Exception as exc:  # pragma: no cover - best effort
                logger.error("Failed to process upload: %s", exc)
                msg = f"Error processing {safe_unicode_encode(filename)}: {exc}"
                cls = "drag-drop-upload drag-drop-upload--error"
                return msg, 0, "0%", cls

    # ------------------------------------------------------------------
    def _process_file(self, content: str, filename: str) -> pd.DataFrame:
        """Decode ``content`` and return a DataFrame."""

        if "," not in content:
            raise ValueError("Invalid content")

        _prefix, data = content.split(",", 1)
        decoded = base64.b64decode(data)
        ext = filename.lower().split(".")[-1]

        if ext == "csv":
            df = pd.read_csv(io.BytesIO(decoded))
        elif ext in {"xls", "xlsx"}:
            df = pd.read_excel(io.BytesIO(decoded))
        elif ext == "json":
            df = pd.read_json(io.BytesIO(decoded))
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return df


# Convenience ---------------------------------------------------------------

def create_upload_component(upload_id: str = "file-upload") -> FileUploadComponent:
    """Return :class:`FileUploadComponent` instance."""

    return FileUploadComponent(upload_id)


__all__ = ["FileUploadComponent", "create_upload_component"]
