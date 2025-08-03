"""Backward compatibility wrapper for ``UploadOrchestrator``."""

from __future__ import annotations

import warnings

from .orchestrator import UploadOrchestrator as _UploadOrchestrator


class UploadProcessingService(_UploadOrchestrator):
    """Deprecated alias for :class:`UploadOrchestrator`."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[override]
        warnings.warn(
            "UploadProcessingService is deprecated; use UploadOrchestrator",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


UploadOrchestrator = _UploadOrchestrator

__all__ = ["UploadProcessingService", "UploadOrchestrator"]

