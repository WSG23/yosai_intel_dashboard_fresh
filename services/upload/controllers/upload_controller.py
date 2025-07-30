"""Dash controller for the unified upload page."""

import base64
import io
import json
import logging
from typing import Any, List, Tuple

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, dash_table, html
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)


class UnifiedUploadController:
    """Fixed upload controller with proper callback objects."""

    def __init__(self, callbacks: Any | None = None) -> None:
        self.callbacks = callbacks
        self._progress = 0
        self._files: List[str] = []

    def upload_callbacks(self) -> List[Tuple[Any, Any, Any, Any, str, dict]]:
        def handle_upload(contents, filename):
            if not contents or not filename:
                raise PreventUpdate

            try:
                content_type, content_string = contents.split(",", 1)
                decoded = base64.b64decode(content_string)
                if filename.lower().endswith(".json"):
                    data = json.loads(decoded.decode("utf-8"))
                    df = pd.DataFrame(data)
                else:
                    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            except Exception as exc:
                logger.error("Failed to parse uploaded file: %s", exc)
                return False, {}

            dash_table.DataTable(
                data=df.head().to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns],
                page_size=5,
            )
            return False, df.to_json(date_format="iso", orient="split")

        return [
            (
                handle_upload,
                [
                    Output("to-column-map-btn", "disabled"),
                    Output("uploaded-df-store", "data"),
                ],
                [
                    Input("drag-drop-upload", "contents"),
                    Input("drag-drop-upload", "filename"),
                ],
                [],  # No states
                "file_upload_handle",
                {"prevent_initial_call": True},
            ),
        ]
