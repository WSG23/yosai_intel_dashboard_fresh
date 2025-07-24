"""Utilities for deprecating functions and tracking usage."""

from __future__ import annotations

import functools
import warnings
from typing import Callable, Any

from .performance import get_performance_monitor


def deprecated(
    since: str,
    removal: str | None = None,
    migration: str | None = None,
    track_usage: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Mark a function as deprecated.

    Parameters
    ----------
    since:
        Version when the function was deprecated.
    removal:
        Planned version for removal. If provided, included in the warning
        message.
    migration:
        Optional hint for migrating off the deprecated functionality.
    track_usage:
        If ``True``, each call records a ``deprecated.<func>`` metric via the
        :mod:`core.performance` monitor.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        parts = [f"{func.__module__}.{func.__name__} is deprecated since {since}"]
        if removal:
            parts.append(f"and will be removed in {removal}")
        if migration:
            parts.append(migration)
        message = " ".join(parts)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            if track_usage:
                get_performance_monitor().record_metric(
                    f"deprecated.{func.__name__}", 1
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator
