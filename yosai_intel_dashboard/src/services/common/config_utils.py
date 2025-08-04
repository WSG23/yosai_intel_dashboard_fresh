from __future__ import annotations

"""Shared configuration helpers for validation classes."""

from typing import Any

from yosai_intel_dashboard.src.core.utils import (
    get_ai_confidence_threshold,
    get_max_upload_size_mb,
    get_upload_chunk_size,
)


def create_config_methods(cls: Any) -> Any:
    """No-op kept for backward compatibility."""
    return cls


def common_init(self: Any, config: Any | None = None) -> None:
    """Initialize configuration defaults."""
    self.config = config or {}
    self.max_size_mb = get_max_upload_size_mb(self.config)
    self.ai_threshold = get_ai_confidence_threshold(self.config)
    self.chunk_size = get_upload_chunk_size(self.config)


__all__ = ["create_config_methods", "common_init"]
