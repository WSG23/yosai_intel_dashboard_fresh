"""Backward compatibility wrapper for :class:`UnifiedUploadValidator`."""
from __future__ import annotations

from typing import Any, Optional


from services.data_processing.unified_upload_validator import (
    UnifiedUploadValidator,
    _lazy_string_validator,
)
from upload_types import ValidationResult
from services.configuration_service import (
    ConfigurationServiceProtocol,
    DynamicConfigurationService,
)


def create_config_methods(cls):
    cls.get_ai_confidence_threshold = lambda self: self.ai_threshold
    cls.get_max_upload_size_mb = lambda self: self.max_size_mb
    cls.get_upload_chunk_size = lambda self: self.chunk_size
    return cls


def common_init(self, config=None):
    self.config = config or {}
    self.max_size_mb = self.config.get("max_upload_size_mb", 100)
    self.ai_threshold = self.config.get("ai_confidence_threshold", 0.8)
    self.chunk_size = self.config.get("upload_chunk_size", 1048576)


@create_config_methods
class InputValidator(UnifiedUploadValidator):
    """Thin wrapper around :class:`UnifiedUploadValidator`."""

    def __init__(
        self,
        max_size_mb: Optional[int] = None,
        config: ConfigurationServiceProtocol | None = None,
    ) -> None:
        config = config or DynamicConfigurationService()
        common_init(self, config)
        if max_size_mb is not None:
            self.max_size_mb = max_size_mb
        self._string_validator = _lazy_string_validator()

