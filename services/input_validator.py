"""Backward compatibility wrapper for :class:`UnifiedUploadValidator`."""
from __future__ import annotations

from typing import Any, Optional

from services.data_processing.unified_upload_validator import UnifiedUploadValidator
from upload_types import ValidationResult
from services.configuration_service import (
    ConfigurationServiceProtocol,
    DynamicConfigurationService,
)


class InputValidator(UnifiedUploadValidator):
    """Thin wrapper around :class:`UnifiedUploadValidator`."""

    def __init__(
        self,
        max_size_mb: Optional[int] = None,
        config: ConfigurationServiceProtocol | None = None,
    ) -> None:
        config = config or DynamicConfigurationService()
        super().__init__(max_size_mb=max_size_mb, config=config)
