#!/usr/bin/env python3
"""Utility helpers for monitoring process memory usage."""

import logging

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore


def check_memory_limit(max_mb: int, logger: logging.Logger) -> None:
    """Raise ``MemoryError`` if RSS memory exceeds ``max_mb``."""
    if not psutil:
        return
    mem_mb = psutil.Process().memory_info().rss / (1024 * 1024)
    if mem_mb > max_mb:
        logger.error(
            "Memory usage %.1f MB exceeds limit %s MB", mem_mb, max_mb
        )
        raise MemoryError(
            f"Memory usage {mem_mb:.1f} MB exceeds limit {max_mb} MB"
        )
