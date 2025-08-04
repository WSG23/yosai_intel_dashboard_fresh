from __future__ import annotations

"""Callback manager for the upload domain."""

from typing import Dict

from yosai_intel_dashboard.src.core.callback_registry import (
    CallbackRegistry,
    ComponentCallbackManager,
)
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
    CallbackHandler,
    TrulyUnifiedCallbacks,
)


class UploadCallbacks(ComponentCallbackManager):
    """Register upload related callbacks using :class:`TrulyUnifiedCallbacks`."""

    registry_name = "upload"

    def register_all(self) -> Dict[str, CallbackHandler]:
        callbacks: TrulyUnifiedCallbacks = self.registry.callbacks
        callbacks.register_upload_callbacks()
        return {}


__all__ = ["UploadCallbacks"]
