from __future__ import annotations

"""Utilities for monitoring process memory."""

import logging

try:
    import psutil
except Exception:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore


class MemoryManager:
    """Track memory usage and warn if limits are exceeded."""

    def __init__(self, limit_mb: float | None = None) -> None:
        self.limit_mb = limit_mb
        self.logger = logging.getLogger(__name__)

    def usage_mb(self) -> float:
        if not psutil:
            return 0.0
        try:
            return psutil.Process().memory_info().rss / (1024 * 1024)
        except Exception:  # pragma: no cover - best effort
            return 0.0

    def check_limit(self) -> None:
        if self.limit_mb is None:
            return
        used = self.usage_mb()
        if used > self.limit_mb:
            self.logger.warning(
                f"Memory usage {used:.1f} MB exceeds limit {self.limit_mb:.1f} MB"
            )


__all__ = ["MemoryManager"]
