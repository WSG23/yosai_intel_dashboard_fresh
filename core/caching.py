"""Caching utilities for performance optimization"""

import functools
import threading
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional


class MemoryCache:
    """Thread-safe in-memory cache implementation"""

    def __init__(self, default_ttl: int = 300) -> None:
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""

        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                return None

            return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""

        with self._lock:
            expiry = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
            self._cache[key] = {"value": value, "expiry": expiry}

    def delete(self, key: str) -> bool:
        """Delete key from cache"""

        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries"""

        with self._lock:
            self._cache.clear()

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""

        return datetime.now() > entry["expiry"]


def cached(ttl: int = 300, key_func: Optional[Callable] = None) -> Callable:
    """Decorator for caching function results"""

    def decorator(func: Callable) -> Callable:
        cache = MemoryCache(ttl)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = (
                    f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                )

            result = cache.get(cache_key)
            if result is not None:
                return result

            # Avoid duplicate computation for the same key by holding the
            # cache lock while checking/setting the value.
            with cache._lock:
                result = cache.get(cache_key)
                if result is not None:
                    return result

                result = func(*args, **kwargs)
                cache.set(cache_key, result)
                return result

        wrapper.cache = cache
        return wrapper

    return decorator
