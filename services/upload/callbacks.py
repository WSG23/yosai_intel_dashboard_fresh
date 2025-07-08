from __future__ import annotations

"""Callback manager for the upload domain."""

from core.callback_registry import CallbackRegistry, ComponentCallbackManager
from upload_callbacks import UploadCallbackManager


class UploadCallbacks(ComponentCallbackManager):
    """Register upload related callbacks using :class:`UploadCallbackManager`."""

    def register_all(self) -> None:
        manager = UploadCallbackManager()
        manager.register(self.registry)


__all__ = ["UploadCallbacks"]
