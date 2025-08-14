from __future__ import annotations

"""Shared configuration helper functions.

This module hosts lightweight helpers that access values from the dynamic
configuration system. Keeping these helpers in a standalone module avoids
import cycles when other modules need to reference configuration values.
"""

from typing import TYPE_CHECKING

from yosai_intel_dashboard.src.core.container import container
from yosai_intel_dashboard.src.core.protocols import ConfigurationProtocol
from yosai_intel_dashboard.src.infrastructure.config.config import (
    get_analytics_config,
)

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
        DynamicConfigManager,
    )


def _dynamic_config() -> "DynamicConfigManager":
    """Return the :class:`DynamicConfigManager` from the DI container."""
    if container.has("dynamic_config"):
        return container.get("dynamic_config")
    from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
        dynamic_config,
    )

    return dynamic_config


def get_max_parallel_uploads() -> int:
    """Return the maximum number of parallel uploads from the dynamic configuration."""
    return _dynamic_config().get_max_parallel_uploads()


def get_validator_rules() -> dict:
    """Return validator rules for uploads from the dynamic configuration."""
    return _dynamic_config().get_validator_rules()


def get_max_upload_size_bytes() -> int:
    """Return the maximum upload size in bytes from the dynamic configuration."""
    return _dynamic_config().get_max_upload_size_bytes()


def validate_large_file_support() -> bool:
    """Return ``True`` if large file uploads are supported."""
    return _dynamic_config().validate_large_file_support()


def get_db_pool_size() -> int:
    """Return the configured database pool size."""
    return _dynamic_config().get_db_pool_size()


def get_max_display_rows(
    config: ConfigurationProtocol | None = None,
) -> int:
    """Return maximum number of rows to show in previews."""
    try:
        cfg = config or _dynamic_config()
        return (
            get_analytics_config().max_display_rows or cfg.analytics.max_display_rows
        )
    except Exception:
        cfg = config or _dynamic_config()
        return cfg.analytics.max_display_rows


__all__ = [
    "get_max_parallel_uploads",
    "get_validator_rules",
    "get_max_upload_size_bytes",
    "validate_large_file_support",
    "get_db_pool_size",
    "get_max_display_rows",
]

