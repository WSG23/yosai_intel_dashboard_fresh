from __future__ import annotations

from typing import Any, Dict

from config.dynamic_config import DynamicConfigManager, dynamic_config
from core.protocols import ConfigurationServiceProtocol


class DynamicConfigurationService(ConfigurationServiceProtocol):
    """Expose :class:`DynamicConfigManager` via ``ConfigurationServiceProtocol``."""

    def __init__(self, manager: DynamicConfigManager = dynamic_config) -> None:
        self._cfg = manager

    # Simple pass-through wrappers
    def get_max_upload_size_mb(self) -> int:
        return self._cfg.get_max_upload_size_mb()

    def get_max_upload_size_bytes(self) -> int:
        return self._cfg.get_max_upload_size_bytes()

    def validate_large_file_support(self) -> bool:
        return self._cfg.validate_large_file_support()

    def get_upload_chunk_size(self) -> int:
        return self._cfg.get_upload_chunk_size()

    def get_max_parallel_uploads(self) -> int:
        return self._cfg.get_max_parallel_uploads()

    def get_validator_rules(self) -> Dict[str, Any]:
        return self._cfg.get_validator_rules()

    def get_ai_confidence_threshold(self) -> int:
        return self._cfg.get_ai_confidence_threshold()

    def get_db_pool_size(self) -> int:
        return self._cfg.get_db_pool_size()


__all__ = [
    "ConfigurationServiceProtocol",
    "DynamicConfigurationService",
]
