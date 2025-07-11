"""Unified upload callbacks handling simple multi-step workflow."""

from __future__ import annotations

import base64
import io
import json
import logging
from typing import Any, List, Tuple

import pandas as pd
import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html, no_update

from ..protocols import UploadControllerProtocol
from dash.dependencies import Input, Output

logger = logging.getLogger(__name__)


class UnifiedUploadController(UploadControllerProtocol):
    """Expose grouped callback definitions for registration."""

    def __init__(self, callbacks: Any | None = None) -> None:
        self.callbacks = callbacks
        self._progress = 0
        self._files: List[str] = []

    # -----------------------------------------------------
    def upload_callbacks(self) -> List[Tuple[Any, Any, Any, Any, str, dict]]:
        def handle_upload(contents: str | None, filename: str | None):
            if not contents or not filename:
                return dash_table.DataTable(data=[]), False, []
            try:
                content_type, content_string = contents.split(",", 1)
                decoded = base64.b64decode(content_string)
                if filename.lower().endswith(".json"):
                    data = json.loads(decoded.decode("utf-8"))
                    df = pd.DataFrame(data)
                else:
                    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            except Exception as exc:  # pragma: no cover - best effort
                logger.error("Failed to parse uploaded file: %s", exc)
                return dash_table.DataTable(data=[]), False, []

            preview = dash_table.DataTable(
                data=df.head().to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns],
                page_size=5,
            )
            return preview, True, df.to_json(date_format="iso", orient="split")

        return [
            (
                handle_upload,
                [
                    Output("preview-area", "children"),
                    Output("to-column-map-btn", "disabled"),
                    Output("uploaded-df-store", "data"),
                ],
                [
                    Input("drag-drop-upload", "contents"),
                    Input("drag-drop-upload", "filename"),
                ],
                None,
                "file_upload_handle",
                {"prevent_initial_call": True},
            ),
        ]

    # -----------------------------------------------------
    def progress_callbacks(self) -> List[Tuple[Any, Any, Any, Any, str, dict]]:
        def update_progress(n_intervals: int):
            self._progress = min(100, self._progress + 20)
            items = [html.Li(f"Processed {p}") for p in self._files]
            done = self._progress >= 100
            disabled = not done
            return self._progress, f"{self._progress}%", items, disabled

        return [
            (
                update_progress,
                [
                    Output("upload-progress", "value"),
                    Output("upload-progress", "label"),
                    Output("file-progress-list", "children"),
                    Output("progress-done-trigger", "disabled"),
                ],
                Input("upload-progress-interval", "n_intervals"),
                None,
                "file_upload_progress",
                {"prevent_initial_call": True},
            ),
        ]

    # -----------------------------------------------------
    def validation_callbacks(self) -> List[Tuple[Any, Any, Any, Any, str, dict]]:
        def finalize_upload(n_clicks: int):
            if not n_clicks:
                return no_update, no_update, no_update
            return True, {"display": "none"}, {"display": "block"}

        return [
            (
                finalize_upload,
                [
                    Output("upload-progress-interval", "disabled"),
                    Output("upload-progress", "style"),
                    Output("preview-area", "style"),
                ],
                Input("progress-done-trigger", "n_clicks"),
                None,
                "file_upload_finalize",
                {"prevent_initial_call": True},
            ),
        ]

    # -----------------------------------------------------------------
    def process_uploaded_files(
        self,
        contents_list: List[str],
        filenames_list: List[str],
    ) -> Tuple[List[Any], List[Any], Dict[str, Any], Dict[str, Any]]:
        """Placeholder implementation for protocol compliance."""
        return [], [], {}, {}


__all__ = ["UnifiedUploadController"]
