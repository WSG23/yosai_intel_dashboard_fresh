"""Central manager for registering Dash callbacks."""

from __future__ import annotations

from typing import Any

from dash.dependencies import Input, Output, State

from components.simple_device_mapping import (
    register_callbacks as register_device_callbacks,
)
from ui.callbacks.column_callbacks import toggle_custom_field
from ui.callbacks.file_callbacks import UploadCallbackManager
from yosai_intel_dashboard.src.core.truly_unified_callbacks import TrulyUnifiedCallbacks


class CallbackManager:
    """Aggregate application callbacks."""

    def __init__(self, service: Any) -> None:
        self.service = service

    def register_all(self, manager: TrulyUnifiedCallbacks) -> None:
        register_device_callbacks(manager)
        UploadCallbackManager().register(manager)
