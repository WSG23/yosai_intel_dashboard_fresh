"""Shim for registering upload-related callbacks."""
from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


class UploadCallbackManager:
    """Register callbacks from :class:`UnifiedUploadController`."""

    def register(self, manager: Any, controller: Any | None = None) -> None:
        try:
            from services.upload.controllers.upload_controller import UnifiedUploadController
        except Exception as exc:  # pragma: no cover - import errors logged
            logger.error("Failed to import UnifiedUploadController: %s", exc)
            return

        uc = UnifiedUploadController(callbacks=manager)

        callback_sources = [
            getattr(uc, "upload_callbacks", lambda: [])(),
            getattr(uc, "progress_callbacks", lambda: [])(),
            getattr(uc, "validation_callbacks", lambda: [])(),
        ]

        for defs in callback_sources:
            for func, outputs, inputs, states, cid, extra in defs:
                manager.register_callback(
                    outputs,
                    inputs,
                    states,
                    callback_id=cid,
                    component_name="file_upload",
                    **extra,
                )(func)


__all__ = ["UploadCallbackManager"]
