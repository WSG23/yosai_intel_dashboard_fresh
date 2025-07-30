from __future__ import annotations

"""Helpers to resolve common configuration values."""

from typing import Any

from core.config import get_ai_confidence_threshold as default_ai_confidence_threshold
from core.config import get_max_upload_size_mb as default_max_upload_size_mb
from core.config import get_upload_chunk_size as default_upload_chunk_size


def resolve_ai_confidence_threshold(cfg: Any | None = None) -> float:
    """Return the AI confidence threshold from *cfg* or defaults."""
    if cfg is not None:
        if hasattr(cfg, "performance") and hasattr(
            cfg.performance, "ai_confidence_threshold"
        ):
            return cfg.performance.ai_confidence_threshold
        if hasattr(cfg, "ai_threshold"):
            return cfg.ai_threshold
    return default_ai_confidence_threshold()


def resolve_max_upload_size_mb(cfg: Any | None = None) -> int:
    """Return the maximum upload size in MB from *cfg* or defaults."""
    if cfg is not None:
        if hasattr(cfg, "upload") and hasattr(cfg.upload, "max_file_size_mb"):
            return cfg.upload.max_file_size_mb
        if hasattr(cfg, "max_size_mb"):
            return cfg.max_size_mb
        if hasattr(cfg, "security") and hasattr(cfg.security, "max_upload_mb"):
            return cfg.security.max_upload_mb
    return default_max_upload_size_mb()


def resolve_upload_chunk_size(cfg: Any | None = None) -> int:
    """Return the upload chunk size from *cfg* or defaults."""
    if cfg is not None:
        if hasattr(cfg, "uploads") and hasattr(cfg.uploads, "DEFAULT_CHUNK_SIZE"):
            return cfg.uploads.DEFAULT_CHUNK_SIZE
        if hasattr(cfg, "chunk_size"):
            return cfg.chunk_size
    return default_upload_chunk_size()


__all__ = [
    "resolve_ai_confidence_threshold",
    "resolve_max_upload_size_mb",
    "resolve_upload_chunk_size",
]
