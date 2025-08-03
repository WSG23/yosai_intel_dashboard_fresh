"""Backward compatibility wrapper for ``UploadProcessingService``."""

from __future__ import annotations

import warnings

from .core.processor import UploadProcessingService as _UploadProcessingService


class UploadProcessingService(_UploadProcessingService):
    """Deprecated alias for :class:`core.processor.UploadProcessingService`."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[override]
        warnings.warn(
            "services.upload.processing.UploadProcessingService is deprecated; "
            "use services.upload.core.processor.UploadProcessingService",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


__all__ = ["UploadProcessingService"]

