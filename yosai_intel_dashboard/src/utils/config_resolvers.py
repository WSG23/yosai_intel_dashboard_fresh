from __future__ import annotations

"""Helpers to resolve common configuration values."""

from typing import Any, Callable


def _default_value(resolver: Callable[[], Any] | None, fallback: Any) -> Any:
    """Return a value from *resolver* or *fallback* on error."""
    if resolver is not None:
        try:
            return resolver()
        except Exception:
            return fallback
    return fallback


def _default_max_upload_size_mb(resolver: Callable[[], int] | None) -> int:
    return _default_value(resolver, 0)


def _default_upload_chunk_size(resolver: Callable[[], int] | None) -> int:
    return _default_value(resolver, 0)


def resolve_ai_confidence_threshold(
    cfg: Any | None = None,
    *,
    default_resolver: Callable[[], float] | None = None,
) -> float:
    """Return the AI confidence threshold from *cfg* or defaults."""
    if cfg is not None:
        if hasattr(cfg, "performance") and hasattr(
            cfg.performance, "ai_confidence_threshold"
        ):
            return cfg.performance.ai_confidence_threshold
        if hasattr(cfg, "ai_threshold"):
            return cfg.ai_threshold
    return _default_value(default_resolver, 0.0)


def resolve_max_upload_size_mb(
    cfg: Any | None = None,
    *,
    default_resolver: Callable[[], int] | None = None,
) -> int:
    """Return the maximum upload size in MB from *cfg* or defaults."""
    if cfg is not None:
        if hasattr(cfg, "upload") and hasattr(cfg.upload, "max_file_size_mb"):
            return cfg.upload.max_file_size_mb
        if hasattr(cfg, "max_size_mb"):
            return cfg.max_size_mb
        if hasattr(cfg, "security") and hasattr(cfg.security, "max_upload_mb"):
            return cfg.security.max_upload_mb
    return _default_max_upload_size_mb(default_resolver)


def resolve_upload_chunk_size(
    cfg: Any | None = None,
    *,
    default_resolver: Callable[[], int] | None = None,
) -> int:
    """Return the upload chunk size from *cfg* or defaults."""
    if cfg is not None:
        if hasattr(cfg, "uploads") and hasattr(cfg.uploads, "DEFAULT_CHUNK_SIZE"):
            return cfg.uploads.DEFAULT_CHUNK_SIZE
        if hasattr(cfg, "chunk_size"):
            return cfg.chunk_size
    return _default_upload_chunk_size(default_resolver)


__all__ = [
    "resolve_ai_confidence_threshold",
    "resolve_max_upload_size_mb",
    "resolve_upload_chunk_size",
]
