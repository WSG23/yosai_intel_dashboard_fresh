"""Simple caching helpers with optional Redis backend."""

from __future__ import annotations

import functools
import os
import json
from threading import RLock
from typing import Any, Callable, Optional

from prometheus_client import Counter
from core.performance import cache_monitor

import redis

from core.cache import cache

_locks: dict[str, RLock] = {}
_redis_client: Optional[redis.Redis] = None

cache_hits = Counter(
    "dashboard_cache_hits_total",
    "Number of cache hits",
    ["endpoint"],
)
cache_misses = Counter(
    "dashboard_cache_misses_total",
    "Number of cache misses",
    ["endpoint"],
)


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


def cache_with_lock(ttl_seconds: int = 300, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Cache function results with a per-function lock.

    The TTL can be overridden by setting an environment variable named
    ``CACHE_TTL_<NAME>`` where ``NAME`` defaults to the decorated function
    name in uppercase.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func_name = func.__name__
        lock = _get_lock(func_name)
        env_var = f"CACHE_TTL_{(name or func_name).upper()}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = (
                f"{func.__module__}.{func_name}:"
                f"{hash(str(args) + str(sorted(kwargs.items())))}"
            )
            result = get_cache_value(key)
            if result is not None:
                cache_monitor.record_cache_hit(func_name)
                cache_hits.labels(func_name).inc()
                return result

            with lock:
                result = get_cache_value(key)
                if result is not None:
                    cache_monitor.record_cache_hit(func_name)
                    cache_hits.labels(func_name).inc()
                    return result

                cache_monitor.record_cache_miss(func_name)
                cache_misses.labels(func_name).inc()
                result = func(*args, **kwargs)
                override = os.getenv(env_var)
                effective_ttl = int(override) if override and override.isdigit() else ttl_seconds
                set_cache_value(key, result, effective_ttl)
                return result

        return wrapper

    return decorator

__all__ = [
    "cache_with_lock",
    "get_cache_value",
    "set_cache_value",
    "delete_cache_key",
    "clear_cache",
    "cache_hits",
    "cache_misses",
]
