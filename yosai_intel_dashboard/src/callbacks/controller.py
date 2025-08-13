"""Unified callback controller collecting page callbacks."""
from __future__ import annotations

from dash import Input, Output, callback_context, html
from dash.exceptions import PreventUpdate

from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
    TrulyUnifiedCallbacks,
)


def register_greetings_callbacks(app, container) -> None:
    """Register callbacks for the greetings page."""
    callbacks = TrulyUnifiedCallbacks(app)

    @callbacks.callback(
        Output("greet-output", "children"),
        Input("name-input", "value"),
        callback_id="greet",
        component_name="greetings",
    )
    def _update_greeting(name: str):
        if not name:
            raise PreventUpdate
        svc = container.get("greeting_service") if container else None
        if svc is None:  # pragma: no cover - defensive
            raise PreventUpdate
        return svc.greet(name)


def register_upload_callbacks(
    app,
    *,
    upload_controller: "UnifiedUploadController" | None = None,
) -> None:
    """Register upload page callbacks."""
    from yosai_intel_dashboard.src.services.upload.controllers.upload_controller import (
        UnifiedUploadController,
    )

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


def register_device_learning_callbacks(app, container) -> None:
    """Register device learning callbacks."""
    # Import heavy dependencies lazily to keep controller lightweight
    import pandas as pd
    from yosai_intel_dashboard.src.core.interfaces.service_protocols import (
        get_device_learning_service,
    )

    callbacks = TrulyUnifiedCallbacks(app)

    @callbacks.callback(
        Output("device-learning-status", "children"),
        [
            Input("file-upload-store", "data"),
            Input("device-mappings-confirmed", "data"),
        ],
        prevent_initial_call=True,
        callback_id="device_learning",
        component_name="device_learning_service",
    )
    def handle_device_learning(upload_data, confirmed_mappings):
        ctx = callback_context
        if not ctx.triggered:
            return ""
        trigger_id = ctx.triggered[0]["prop_id"]
        learning_service = get_device_learning_service(container)
        if "file-upload-store" in trigger_id and upload_data:
            df = pd.DataFrame(upload_data["data"])
            filename = upload_data["filename"]
            if learning_service.apply_to_global_store(df, filename):
                return html.Div(
                    [
                        html.I(className="fas fa-brain me-2", **{"aria-hidden": "true"}),
                        "Learned device mappings applied!",
                    ],
                    className="text-success",
                )
        elif "device-mappings-confirmed" in trigger_id and confirmed_mappings:
            df = pd.DataFrame(confirmed_mappings["original_data"])
            filename = confirmed_mappings["filename"]
            mappings = confirmed_mappings["mappings"]
            fingerprint = learning_service.save_complete_mapping(df, filename, mappings)
            return html.Div(
                [
                    html.I(className="fas fa-save me-2", **{"aria-hidden": "true"}),
                    f"Mappings saved! ID: {fingerprint[:8]}",
                ],
                className="text-success",
            )
        return ""


def register_callbacks(app, container) -> None:
    """Register callbacks for all core pages."""
    register_greetings_callbacks(app, container)
    register_upload_callbacks(app)
    register_device_learning_callbacks(app, container)
