"""Central manager for registering Dash callbacks."""

from __future__ import annotations

from typing import Any

from dash.dependencies import Input, Output, State

from core.truly_unified_callbacks import TrulyUnifiedCallbacks

from .device_callbacks import toggle_simple_device_modal
from .file_callbacks import UploadCallbackManager


class MappingCallbackManager:
    """Aggregate application callbacks."""

    def __init__(self, service: Any | None = None) -> None:
        self.service = service

    def register_all(self, manager: TrulyUnifiedCallbacks) -> None:
        manager.register_callback(  # type: ignore[misc]
            Output("simple-device-modal", "is_open"),
            [
                Input("open-device-mapping", "n_clicks"),
                Input("device-modal-cancel", "n_clicks"),
                Input("device-modal-save", "n_clicks"),
            ],
            [State("simple-device-modal", "is_open")],
            callback_id="toggle_simple_device_modal",
            component_name="device_components",
        )(toggle_simple_device_modal)

        UploadCallbackManager().register(manager)

    @classmethod
    def register_all_callbacks(cls, app: Any) -> None:
        manager = TrulyUnifiedCallbacks(app)
        cls().register_all(manager)
