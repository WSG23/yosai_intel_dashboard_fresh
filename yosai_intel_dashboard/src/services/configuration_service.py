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
from yosai_intel_dashboard.src.infrastructure.config.utils import (
    get_ai_confidence_threshold as _get_ai_confidence_threshold,
)
from yosai_intel_dashboard.src.infrastructure.config.utils import (
    get_upload_chunk_size as _get_upload_chunk_size,
)


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
        return _get_upload_chunk_size(self._cfg)

    def get_max_parallel_uploads(self) -> int:
        return self._cfg.get_max_parallel_uploads()

    def get_validator_rules(self) -> Dict[str, Any]:
        return self._cfg.get_validator_rules()

    def get_ai_confidence_threshold(self) -> int:
        return _get_ai_confidence_threshold(self._cfg)

    def get_db_pool_size(self) -> int:
        return self._cfg.get_db_pool_size()


__all__ = [
    "ConfigurationServiceProtocol",
    "DynamicConfigurationService",
]
