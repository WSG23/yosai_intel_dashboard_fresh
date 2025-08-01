from __future__ import annotations

"""Callback manager for the upload domain."""

from yosai_intel_dashboard.src.core.callback_registry import CallbackRegistry, ComponentCallbackManager
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks


class UploadCallbacks(ComponentCallbackManager):
    """Register upload related callbacks using :class:`TrulyUnifiedCallbacks`."""

    def register_all(self) -> None:
        callbacks: TrulyUnifiedCallbacks = self.registry.callbacks
        callbacks.register_upload_callbacks()


__all__ = ["UploadCallbacks"]
