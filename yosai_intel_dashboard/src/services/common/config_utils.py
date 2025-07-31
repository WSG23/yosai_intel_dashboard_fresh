from __future__ import annotations

"""Shared configuration helpers for validation classes."""

from typing import Any


def create_config_methods(cls: Any) -> Any:
    """Attach legacy accessor methods used across validators."""
    cls.get_ai_confidence_threshold = lambda self: self.ai_threshold
    cls.get_max_upload_size_mb = lambda self: self.max_size_mb
    cls.get_upload_chunk_size = lambda self: self.chunk_size
    return cls


def common_init(self: Any, config: Any | None = None) -> None:
    """Initialize configuration defaults."""
    self.config = config or {}
    self.max_size_mb = self.config.get("max_upload_size_mb", 100)
    self.ai_threshold = self.config.get("ai_confidence_threshold", 0.8)
    self.chunk_size = self.config.get("upload_chunk_size", 1048576)


__all__ = ["create_config_methods", "common_init"]
