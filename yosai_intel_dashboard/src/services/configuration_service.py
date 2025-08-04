"""Configuration service facade.

See ADR-0002 for design decisions around ConfigService.
"""

from __future__ import annotations

from typing import Any, Dict

from yosai_intel_dashboard.src.core.interfaces.protocols import (
    ConfigurationServiceProtocol,
)
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
    DynamicConfigManager,
    dynamic_config,
)
from src.common.config import ConfigProvider, ConfigService


class DynamicConfigurationService(ConfigurationServiceProtocol):
    """Expose configuration values via ``ConfigurationServiceProtocol``."""

    def __init__(
        self,
        manager: DynamicConfigManager = dynamic_config,
        cfg: ConfigProvider | None = None,
    ) -> None:
        self._manager = manager
        self._cfg = cfg or ConfigService()

    # Simple pass-through wrappers
    @property
    def max_upload_size_mb(self) -> int:
        return self._cfg.max_upload_size_mb

    def get_max_upload_size_bytes(self) -> int:
        return self._cfg.max_upload_size_mb * 1024 * 1024

    def validate_large_file_support(self) -> bool:
        return self._cfg.max_upload_size_mb >= 50

    @property
    def upload_chunk_size(self) -> int:
        return self._cfg.upload_chunk_size

    def get_max_parallel_uploads(self) -> int:
        return self._manager.get_max_parallel_uploads()

    def get_validator_rules(self) -> Dict[str, Any]:
        return self._manager.get_validator_rules()

    @property
    def ai_confidence_threshold(self) -> int:
        return self._cfg.ai_confidence_threshold

    def get_db_pool_size(self) -> int:
        return self._manager.get_db_pool_size()


__all__ = [
    "ConfigurationServiceProtocol",
    "DynamicConfigurationService",
]
