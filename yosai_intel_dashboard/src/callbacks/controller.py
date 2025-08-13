from __future__ import annotations

"""Central registry for Dash callbacks."""

from dataclasses import dataclass

import pandas as pd
from dash import Input, Output, callback_context, html
from dash.exceptions import PreventUpdate

try:  # pragma: no cover - optional dependency during minimal tests
    from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
        TrulyUnifiedCallbacks,
    )
except Exception:  # pragma: no cover - fallback when core package missing

    class TrulyUnifiedCallbacks:  # type: ignore[too-few-public-methods]
        """Minimal stub used when core package isn't available."""

        def __init__(self, app=None):
            self.app = app

        def callback(self, *args, **kwargs):
            def decorator(func):
                if self.app is not None:
                    return self.app.callback(*args, **kwargs)(func)
                return func

            return decorator

        register_handler = callback


@dataclass(frozen=True)
class GreetingIds:
    """DOM ids used by greeting callbacks."""

    name_input: str = "name-input"
    greet_output: str = "greet-output"


@dataclass(frozen=True)
class UploadIds:
    """DOM ids used by upload callbacks."""

    drag_drop: str = "drag-drop-upload"
    to_column_map_btn: str = "to-column-map-btn"
    uploaded_store: str = "uploaded-df-store"


@dataclass(frozen=True)
class DeviceLearningIds:
    """DOM ids used by device learning callbacks."""

    status: str = "device-learning-status"
    file_upload_store: str = "file-upload-store"
    confirmed: str = "device-mappings-confirmed"


@dataclass(frozen=True)
class CallbackIds:
    """Container for all callback id groups."""

    greeting: GreetingIds = GreetingIds()
    upload: UploadIds = UploadIds()
    device_learning: DeviceLearningIds = DeviceLearningIds()


def register_greeting_callbacks(
    callbacks: TrulyUnifiedCallbacks,
    container,
    ids: GreetingIds = GreetingIds(),
) -> None:
    """Register callbacks for the greeting page."""
    from yosai_intel_dashboard.src.simple_di import inject

    @callbacks.callback(
        Output(ids.greet_output, "children"),
        Input(ids.name_input, "value"),
        callback_id="greet",
        component_name="greetings",
    )
    @inject(container=container)
    def _update_greeting(name: str, svc):
        if not name:
            raise PreventUpdate
        return svc.greet(name)


def register_upload_callbacks(
    callbacks: TrulyUnifiedCallbacks,
    *,
    upload_controller=None,
    ids: UploadIds = UploadIds(),
) -> None:
    """Register callbacks for file uploads."""
    from yosai_intel_dashboard.src.services.upload.controllers.upload_controller import (
        UnifiedUploadController,
    )

    controller = upload_controller or UnifiedUploadController()

    @callbacks.callback(
        [Output(ids.to_column_map_btn, "disabled"), Output(ids.uploaded_store, "data")],
        [Input(ids.drag_drop, "contents"), Input(ids.drag_drop, "filename")],
        callback_id="file_upload_handle",
        component_name="file_upload",
        prevent_initial_call=True,
    )
    def handle_upload(contents, filename):
        df = controller.parse_upload(contents, filename)
        if df is None:
            raise PreventUpdate
        return False, df.to_json(date_format="iso", orient="split")


def register_device_learning_callbacks(
    callbacks: TrulyUnifiedCallbacks,
    container,
    ids: DeviceLearningIds = DeviceLearningIds(),
) -> None:
    """Register callbacks for device learning workflow."""
    from yosai_intel_dashboard.src.core.interfaces.service_protocols import (
        get_device_learning_service,
    )

    @callbacks.callback(
        Output(ids.status, "children"),
        [Input(ids.file_upload_store, "data"), Input(ids.confirmed, "data")],
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

        if ids.file_upload_store in trigger_id and upload_data:
            df = pd.DataFrame(upload_data["data"])
            filename = upload_data["filename"]
            if learning_service.apply_to_global_store(df, filename):
                return html.Div(
                    [
                        html.I(
                            className="fas fa-brain me-2", **{"aria-hidden": "true"}
                        ),
                        "Learned device mappings applied!",
                    ],
                    className="text-success",
                )
        elif ids.confirmed in trigger_id and confirmed_mappings:
            df = pd.DataFrame(confirmed_mappings["original_data"])
            filename = confirmed_mappings["filename"]
            mappings = confirmed_mappings["mappings"]
            fingerprint = learning_service.save_complete_mapping(
                df, filename, mappings
            )
            return html.Div(
                [
                    html.I(className="fas fa-save me-2", **{"aria-hidden": "true"}),
                    f"Mappings saved! ID: {fingerprint[:8]}",
                ],
                className="text-success",
            )
        return ""


def register_callbacks(
    app,
    container,
    *,
    constants: CallbackIds = CallbackIds(),
    upload_controller=None,
) -> None:
    """Register all callbacks with the provided app instance."""
    callbacks = TrulyUnifiedCallbacks(app)
    register_greeting_callbacks(callbacks, container, constants.greeting)
    register_upload_callbacks(
        callbacks, upload_controller=upload_controller, ids=constants.upload
    )
    register_device_learning_callbacks(
        callbacks, container, ids=constants.device_learning
    )


__all__ = [
    "CallbackIds",
    "DeviceLearningIds",
    "GreetingIds",
    "UploadIds",
    "register_callbacks",
    "register_device_learning_callbacks",
    "register_greeting_callbacks",
    "register_upload_callbacks",
]
