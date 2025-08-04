from __future__ import annotations

"""Utility helpers for resolving configuration values.

These functions provide a single place to retrieve common configuration
settings.  They accept any object or mapping that exposes the relevant
attributes and fall back to defaults from :class:`ConfigService` when a value
is not provided.
"""

from typing import Any, Mapping

from src.common.config import ConfigService


_default_cfg = ConfigService()


def _mapping_or_attr(cfg: Any, attr: str, default: Any) -> Any:
    """Return *attr* from *cfg* supporting mappings and attributes."""
    if cfg is None:
        return default
    if isinstance(cfg, Mapping):
        return cfg.get(attr, default)
    return getattr(cfg, attr, default)


def get_ai_confidence_threshold(cfg: Any | None = None) -> float:
    """Return the AI confidence threshold from *cfg* or defaults."""
    default = _default_cfg.ai_confidence_threshold
    if cfg is None:
        return default
    if isinstance(cfg, Mapping):
        return float(cfg.get("ai_confidence_threshold", default))
    if hasattr(cfg, "performance") and hasattr(
        cfg.performance, "ai_confidence_threshold"
    ):
        return float(cfg.performance.ai_confidence_threshold)
    if hasattr(cfg, "ai_confidence_threshold"):
        return float(cfg.ai_confidence_threshold)
    if hasattr(cfg, "ai_threshold"):
        return float(cfg.ai_threshold)
    return default


def get_max_upload_size_mb(cfg: Any | None = None) -> int:
    """Return the maximum upload size in megabytes from *cfg* or defaults."""
    default = _default_cfg.max_upload_size_mb
    if cfg is None:
        return default
    if isinstance(cfg, Mapping):
        return int(cfg.get("max_upload_size_mb", default))
    if hasattr(cfg, "max_upload_size_mb"):
        return int(cfg.max_upload_size_mb)
    if hasattr(cfg, "max_size_mb"):
        return int(cfg.max_size_mb)
    if hasattr(cfg, "security") and hasattr(cfg.security, "max_upload_mb"):
        return int(cfg.security.max_upload_mb)
    if hasattr(cfg, "upload") and hasattr(cfg.upload, "max_file_size_mb"):
        return int(cfg.upload.max_file_size_mb)
    return default


def get_upload_chunk_size(cfg: Any | None = None) -> int:
    """Return the upload chunk size from *cfg* or defaults."""
    default = _default_cfg.upload_chunk_size
    if cfg is None:
        return default
    if isinstance(cfg, Mapping):
        return int(cfg.get("upload_chunk_size", default))
    if hasattr(cfg, "upload_chunk_size"):
        return int(cfg.upload_chunk_size)
    if hasattr(cfg, "chunk_size"):
        return int(cfg.chunk_size)
    if hasattr(cfg, "uploads") and hasattr(cfg.uploads, "DEFAULT_CHUNK_SIZE"):
        return int(cfg.uploads.DEFAULT_CHUNK_SIZE)
    return default


__all__ = [
    "get_ai_confidence_threshold",
    "get_max_upload_size_mb",
    "get_upload_chunk_size",
]
