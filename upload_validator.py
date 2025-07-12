"""Compatibility wrapper around :class:`UnifiedUploadValidator`."""
from __future__ import annotations

from typing import Optional, Any

from config.dynamic_config import dynamic_config
from core.protocols import ConfigurationProtocol
from services.data_processing.unified_upload_validator import UnifiedUploadValidator
from upload_types import ValidationResult


class UploadValidator(UnifiedUploadValidator):
    """Thin wrapper preserving the old ``UploadValidator`` API."""

    def __init__(
        self,
        max_size_mb: Optional[int] = None,
        config: ConfigurationProtocol = dynamic_config,
    ) -> None:
        super().__init__(max_size_mb=max_size_mb, config=config)
