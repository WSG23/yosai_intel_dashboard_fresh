import functools
import warnings
from typing import Callable

from yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.deprecation import (
    record_deprecated_call,
)

from .performance import MetricType, get_performance_monitor


def deprecated(reason: str | None = None) -> Callable[[Callable], Callable]:
    """Decorator to mark functions as deprecated and record usage metrics."""

    def decorator(func: Callable) -> Callable:
        message = f"{func.__module__}.{func.__name__} is deprecated" + (
            f": {reason}" if reason else ""
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            get_performance_monitor().record_metric(
                message,
                1,
                MetricType.DEPRECATED_USAGE,
                metadata={"function": f"{func.__module__}.{func.__name__}"},
            )
            record_deprecated_call(func.__name__)

            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["deprecated"]
