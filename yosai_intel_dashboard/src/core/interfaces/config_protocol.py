from __future__ import annotations

from typing import Protocol


class ConfigurationProtocol(Protocol):
    """Minimal protocol for accessing runtime configuration values."""

    def get_ai_confidence_threshold(self) -> float:
        """Return the configured AI confidence threshold."""
        ...

    def get_max_upload_size_mb(self) -> int:
        """Return the maximum allowed upload size in megabytes."""
        ...

    def get_upload_chunk_size(self) -> int:
        """Return the configured upload chunk size in bytes."""
        ...


__all__ = ["ConfigurationProtocol"]
