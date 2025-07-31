#!/usr/bin/env python3
"""Utility helpers for monitoring process memory usage."""

import logging
from functools import wraps

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
        logger.error(f"Memory usage {mem_mb:.1f} MB exceeds limit {max_mb} MB")
        raise MemoryError(f"Memory usage {mem_mb:.1f} MB exceeds limit {max_mb} MB")


def memory_safe(max_memory_mb: int) -> callable:
    """Decorator to abort execution when memory usage exceeds ``max_memory_mb``."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            check_memory_limit(max_memory_mb, logger)
            result = func(*args, **kwargs)
            check_memory_limit(max_memory_mb, logger)
            return result

        return wrapper

    return decorator


__all__ = ["check_memory_limit", "memory_safe"]
