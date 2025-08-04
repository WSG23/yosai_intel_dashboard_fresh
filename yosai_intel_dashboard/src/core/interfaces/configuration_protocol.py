from __future__ import annotations

"""Protocol for configuration objects exposing common getters."""

from typing import Protocol


class ConfigurationProtocol(Protocol):
    """Standard interface for configuration getters.

    Implementations provide accessors for commonly used configuration values
    while hiding their underlying structure.  This helps decouple components
    from the concrete configuration implementation.
    """

    def get_ai_confidence_threshold(self) -> float:
        """Return the AI confidence threshold."""
        ...

    def get_max_upload_size_mb(self) -> int:
        """Return maximum upload size in megabytes."""
        ...

    def get_upload_chunk_size(self) -> int:
        """Return default upload chunk size in bytes."""
        ...


__all__ = ["ConfigurationProtocol"]
