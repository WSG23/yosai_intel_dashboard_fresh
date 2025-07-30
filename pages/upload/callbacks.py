from __future__ import annotations

"""Upload feature callbacks."""

from dash import Input, Output
from dash.exceptions import PreventUpdate
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from services.upload.controllers.upload_controller import UnifiedUploadController


def register_callbacks(app, container) -> None:
    """Register upload callbacks using the provided Dash *app*."""
    callbacks = TrulyUnifiedCallbacks(app)
    controller = UnifiedUploadController()

    @callbacks.register_handler(
        [Output("to-column-map-btn", "disabled"), Output("uploaded-df-store", "data")],
        [Input("drag-drop-upload", "contents"), Input("drag-drop-upload", "filename")],
        callback_id="file_upload_handle",
        component_name="file_upload",
        prevent_initial_call=True,
    )
    def handle_upload(contents, filename):
        df = controller.parse_upload(contents, filename)
        if df is None:
            raise PreventUpdate
        return False, df.to_json(date_format="iso", orient="split")
