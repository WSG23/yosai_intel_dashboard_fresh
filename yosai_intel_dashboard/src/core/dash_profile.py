import asyncio
import logging
import time
from functools import wraps


def handle_profile(callback_id: str):
    """Measure runtime of Dash callback functions."""

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                if duration_ms > 100:
                    logging.warning(f"Callback {callback_id} took {duration_ms:.2f} ms")
                return result

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            if duration_ms > 100:
                logging.warning(f"Callback {callback_id} took {duration_ms:.2f} ms")
            return result

        return sync_wrapper

    return decorator


__all__ = ["profile_callback"]

# Alias for backward compatibility
profile_callback = handle_profile
