from __future__ import annotations

"""Shared configuration helper functions."""

from typing import Any

from yosai_intel_dashboard.src.utils.config_resolvers import (
    resolve_ai_confidence_threshold,
    resolve_upload_chunk_size,
)


def get_ai_confidence_threshold(cfg: Any | None = None) -> float:
    """Return the AI confidence threshold for *cfg* or the global config."""
    if cfg is None:
        from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config

        cfg = dynamic_config
    return resolve_ai_confidence_threshold(cfg)


def get_upload_chunk_size(cfg: Any | None = None) -> int:
    """Return the upload chunk size for *cfg* or the global config."""
    if cfg is None:
        from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config

        cfg = dynamic_config
    return resolve_upload_chunk_size(cfg)


__all__ = ["get_ai_confidence_threshold", "get_upload_chunk_size"]
