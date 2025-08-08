from __future__ import annotations

"""Upload feature callbacks."""

from dash import Input, Output
from dash.exceptions import PreventUpdate

from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
    TrulyUnifiedCallbacks,
)
from yosai_intel_dashboard.src.services.upload.controllers.upload_controller import (
    UnifiedUploadController,
)


def register_callbacks(
    app,
    *,
    upload_controller: UnifiedUploadController | None = None,
) -> None:
    """Register upload callbacks using the provided Dash app.

    Parameters
    ----------
    app : Dash
        Dash application instance.
    upload_controller : UnifiedUploadController, optional
        Optional controller dependency injected for testing.
    """
    callbacks = TrulyUnifiedCallbacks(app)
    controller = upload_controller or UnifiedUploadController()

    @callbacks.callback(
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
