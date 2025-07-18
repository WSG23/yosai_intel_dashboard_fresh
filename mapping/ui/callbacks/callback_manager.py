"""Central manager for registering Dash callbacks."""

from __future__ import annotations

from typing import Any

from dash.dependencies import Input, Output, State

from core.truly_unified_callbacks import TrulyUnifiedCallbacks

from .file_callbacks import UploadCallbackManager
from components.simple_device_mapping import register_callbacks as register_device_callbacks


class MappingCallbackManager:
    """Aggregate application callbacks."""

    def __init__(self, service: Any | None = None) -> None:
        self.service = service

    def register_all(self, manager: TrulyUnifiedCallbacks) -> None:
        register_device_callbacks(manager)
        UploadCallbackManager().register(manager)

    @classmethod
    def register_all_callbacks(cls, app: Any) -> None:
        manager = TrulyUnifiedCallbacks(app)
        cls().register_all(manager)
