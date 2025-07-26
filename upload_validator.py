"""Compatibility wrapper around :class:`UnifiedUploadValidator`."""

from __future__ import annotations

from typing import Any, Optional

from config.dynamic_config import dynamic_config
from core.protocols import ConfigurationProtocol
from services.common.config_utils import common_init, create_config_methods
from services.data_processing.unified_upload_validator import UnifiedUploadValidator
from upload_types import ValidationResult

UploadValidator = UnifiedUploadValidator


@create_config_methods
class UploadValidator(UnifiedUploadValidator):
    """Thin wrapper preserving the old ``UploadValidator`` API."""

    def __init__(
        self,
        max_size_mb: Optional[int] = None,
        config: ConfigurationProtocol = dynamic_config,
    ) -> None:
        common_init(self, config)
        if max_size_mb is not None:
            self.max_size_mb = max_size_mb
