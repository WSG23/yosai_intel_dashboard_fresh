from __future__ import annotations

"""Utility helpers for resolving configuration values.

These functions provide a single place to retrieve common configuration
settings.  They accept any object or mapping that exposes the relevant
attributes and fall back to defaults from :class:`ConfigService` when a value
is not provided.
"""

from typing import Any

from src.common.config import ConfigService, ConfigurationMixin
from yosai_intel_dashboard.src.core import registry


_mixin = ConfigurationMixin()


def _resolve_cfg(cfg: Any | None) -> Any:
    if cfg is not None:
        return cfg
    try:
        get = getattr(registry, "get", None)
        if callable(get):
            result = get("config_service")
            if result is not None:
                return result
    except Exception:
        # If the registry is absent or misconfigured fall back to defaults
        pass
    return ConfigService()


def get_ai_confidence_threshold(cfg: Any | None = None) -> float:
    """Return the AI confidence threshold from ``cfg`` or defaults."""
    return _mixin.get_ai_confidence_threshold(_resolve_cfg(cfg))


def get_max_upload_size_mb(cfg: Any | None = None) -> int:
    """Return the maximum upload size in megabytes from ``cfg`` or defaults."""
    return _mixin.get_max_upload_size_mb(_resolve_cfg(cfg))


def get_upload_chunk_size(cfg: Any | None = None) -> int:
    """Return the upload chunk size from ``cfg`` or defaults."""
    return _mixin.get_upload_chunk_size(_resolve_cfg(cfg))


__all__ = [
    "get_ai_confidence_threshold",
    "get_max_upload_size_mb",
    "get_upload_chunk_size",
]
