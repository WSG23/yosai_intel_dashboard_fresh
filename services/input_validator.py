"""Input validation helpers for uploaded files."""

from __future__ import annotations

from typing import Optional

from services.configuration_service import (
    ConfigurationServiceProtocol,
    DynamicConfigurationService,
)
from upload_types import ValidationResult
from services.data_processing.unified_upload_validator import UnifiedUploadValidator


class InputValidator(UnifiedUploadValidator):
    """Thin wrapper around :class:`UnifiedUploadValidator`."""

    def __init__(
        self,
        max_size_mb: Optional[int] = None,
        config: ConfigurationServiceProtocol | None = None,
    ) -> None:
        cfg = config or DynamicConfigurationService()
        super().__init__(max_size_mb=max_size_mb, config=cfg)


__all__ = ["InputValidator", "ValidationResult"]
