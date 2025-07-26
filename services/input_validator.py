"""Backward compatibility wrapper for :class:`UnifiedUploadValidator`."""

from __future__ import annotations

from typing import Any, Optional

from services.common.config_utils import common_init, create_config_methods
from core.protocols import ConfigurationServiceProtocol
from services.configuration_service import DynamicConfigurationService
from services.data_processing.unified_upload_validator import UnifiedUploadValidator
from services.data_processing.validation_utils import _lazy_string_validator
from upload_types import ValidationResult


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
