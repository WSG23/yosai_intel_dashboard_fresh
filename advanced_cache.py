"""Simple caching helpers with optional Redis backend."""

from __future__ import annotations

import functools
import os
import json
from threading import RLock
from typing import Any, Callable, Optional

import redis

from core.cache import cache

_locks: dict[str, RLock] = {}
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Return a lazily initialized Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
            )
            _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client


def get_cache_value(key: str) -> Any:
    client = get_redis_client()
    if client is not None:
        try:
            data = client.get(key)
            if data is not None:
                return json.loads(data.decode("utf-8"))
        except Exception:
            pass
    return cache.get(key)


def set_cache_value(key: str, value: Any, ttl: int | None = None) -> None:
    client = get_redis_client()
    if client is not None:
        try:
            payload = json.dumps(value).encode("utf-8")
            if ttl:
                client.setex(key, ttl, payload)
            else:
                client.set(key, payload)
        except Exception:
            pass
    try:
        cache.set(key, value, timeout=ttl)
    except TypeError:
        cache.set(key, value, ttl=ttl)


def delete_cache_key(key: str) -> None:
    client = get_redis_client()
    if client is not None:
        try:
            client.delete(key)
        except Exception:
            pass
    cache.delete(key)


def clear_cache() -> None:
    client = get_redis_client()
    if client is not None:
        try:
            client.flushdb()
        except Exception:
            pass
    cache.clear()


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
            key = (
                f"{func.__module__}.{func.__name__}:"
                f"{hash(str(args) + str(sorted(kwargs.items())))}"
            )
            result = get_cache_value(key)
            if result is not None:
                return result

            with lock:
                result = get_cache_value(key)
                if result is not None:
                    return result

                result = func(*args, **kwargs)
                set_cache_value(key, result, ttl_seconds)
                return result

        return wrapper

    return decorator

__all__ = [
    "cache_with_lock",
    "get_cache_value",
    "set_cache_value",
    "delete_cache_key",
    "clear_cache",
]
