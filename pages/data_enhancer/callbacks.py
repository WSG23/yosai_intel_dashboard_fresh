from __future__ import annotations

"""Callbacks for the data enhancer feature."""

from dash.dependencies import Input, Output
from dash import html
from dash.exceptions import PreventUpdate

from core.truly_unified_callbacks import TrulyUnifiedCallbacks


def register_callbacks(app, container) -> None:
    """Register data enhancer callbacks."""
    callbacks = TrulyUnifiedCallbacks(app)

    @callbacks.callback(
        Output("upload-status", "children"),
        [Input("upload-data", "contents")],
        [Input("upload-data", "filename")],
        callback_id="handle_file_upload_enhanced",
        component_name="data_enhancer",
    )
    def handle_file_upload(contents, filename):
        if not contents:
            raise PreventUpdate
        return html.Div(f"Received {filename}")

    return None
