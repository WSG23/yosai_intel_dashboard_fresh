from __future__ import annotations

"""Helpers to resolve common configuration values."""

from typing import Any, Callable

from yosai_intel_dashboard.src.core.utils import (
    get_ai_confidence_threshold,
    get_max_upload_size_mb,
    get_upload_chunk_size,
)


def _default_value(resolver: Callable[[], Any] | None, fallback: Any) -> Any:
    """Return a value from *resolver* or *fallback* on error."""
    if resolver is not None:
        try:
            return resolver()
        except Exception:
            return fallback
    return fallback


def resolve_ai_confidence_threshold(
    cfg: Any | None = None,
    *,
    default_resolver: Callable[[], float] | None = None,
) -> float:
    """Return the AI confidence threshold from *cfg* or defaults."""
    if cfg is not None:
        return get_ai_confidence_threshold(cfg)
    return _default_value(default_resolver, get_ai_confidence_threshold(None))


def resolve_max_upload_size_mb(
    cfg: Any | None = None,
    *,
    default_resolver: Callable[[], int] | None = None,
) -> int:
    """Return the maximum upload size in MB from *cfg* or defaults."""
    if cfg is not None:
        return get_max_upload_size_mb(cfg)
    return _default_value(default_resolver, get_max_upload_size_mb(None))


def resolve_upload_chunk_size(
    cfg: Any | None = None,
    *,
    default_resolver: Callable[[], int] | None = None,
) -> int:
    """Return the upload chunk size from *cfg* or defaults."""
    if cfg is not None:
        return get_upload_chunk_size(cfg)
    return _default_value(default_resolver, get_upload_chunk_size(None))


__all__ = [
    "resolve_ai_confidence_threshold",
    "resolve_max_upload_size_mb",
    "resolve_upload_chunk_size",
]
