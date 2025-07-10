import functools
from typing import Any, Callable
from threading import RLock

from core.cache import cache

_locks: dict[str, RLock] = {}


def _get_lock(name: str) -> RLock:
    lock = _locks.get(name)
    if lock is None:
        lock = RLock()
        _locks[name] = lock
    return lock


def cache_with_lock(ttl_seconds: int = 300) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Cache function results with a per-function lock."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        lock = _get_lock(func.__name__)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            result = cache.get(key)
            if result is not None:
                return result

            with lock:
                result = cache.get(key)
                if result is not None:
                    return result

                result = func(*args, **kwargs)
                try:
                    cache.set(key, result, timeout=ttl_seconds)
                except TypeError:
                    # Some cache implementations might use 'ttl'
                    cache.set(key, result, ttl=ttl_seconds)
                return result

        return wrapper

    return decorator

__all__ = ["cache_with_lock"]
