from __future__ import annotations

"""Callback manager for the upload domain."""

from upload_callbacks import UploadCallbackManager
from yosai_intel_dashboard.src.core.callback_registry import (
    CallbackRegistry,
    ComponentCallbackManager,
)


class UploadCallbacks(ComponentCallbackManager):
    """Register upload related callbacks using :class:`UploadCallbackManager`."""

    def register_all(self) -> None:
        manager = UploadCallbackManager()
        manager.register(self.registry)


__all__ = ["UploadCallbacks"]
