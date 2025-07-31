import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def monitor_query_performance(threshold_ms: float = 1000.0):
    """Decorator to monitor database query performance."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000

                if execution_time > threshold_ms:
                    logger.warning(
                        f"Slow query detected: {func.__name__} took {execution_time:.2f}ms"
                    )

                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(
                    f"Query failed: {func.__name__} after {execution_time:.2f}ms: {e}"
                )
                raise

        return wrapper

    return decorator


__all__ = ["monitor_query_performance"]
