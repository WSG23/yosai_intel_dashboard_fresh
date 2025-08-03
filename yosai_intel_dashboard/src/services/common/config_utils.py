from __future__ import annotations

"""Shared configuration helpers for validation classes."""

from typing import Any, Mapping


def create_config_methods(cls: Any) -> Any:
    """No-op kept for backward compatibility."""
    return cls


def common_init(self: Any, config: Any | None = None) -> None:
    """Initialize configuration defaults."""
    self.config = config or {}
    if isinstance(self.config, Mapping):
        self.max_size_mb = self.config.get("max_upload_size_mb", 100)
        self.ai_threshold = self.config.get("ai_confidence_threshold", 0.8)
        self.chunk_size = self.config.get("upload_chunk_size", 1048576)
    else:
        self.max_size_mb = getattr(self.config, "max_upload_size_mb", 100)
        self.ai_threshold = getattr(self.config, "ai_confidence_threshold", 0.8)
        self.chunk_size = getattr(self.config, "upload_chunk_size", 1048576)


__all__ = ["create_config_methods", "common_init"]
