from __future__ import annotations

"""Convenience wrapper for the async file processor."""

from yosai_intel_dashboard.src.services.data_processing.async_file_processor import (
    AsyncFileProcessor as _AsyncFileProcessor,
)


class AsyncFileProcessor(_AsyncFileProcessor):
    """Expose :class:`_AsyncFileProcessor` at the top ``services`` level."""

    pass


__all__ = ["AsyncFileProcessor"]
