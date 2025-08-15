"""Simple cache interface used throughout the application."""

from __future__ import annotations

import logging
import time
import weakref
from typing import Any

from flask_caching import Cache

from .registry import ServiceRegistry
from .performance import cache_monitor

logger = logging.getLogger(__name__)


def get_cache() -> Cache:
    """Return the shared cache instance from the service registry."""

    cache = ServiceRegistry.get("cache")
    if cache is None:
        cache = Cache()
        ServiceRegistry.register("cache", cache)
    return cache


def init_app(app) -> None:
    """Initialize the cache with the given Flask app."""
    cache = get_cache()
    try:
        cache.init_app(
            app,
            config={"CACHE_TYPE": "simple", "CACHE_DEFAULT_TIMEOUT": 300},
        )
    except Exception as exc:  # pragma: no cover - fallback
        logger.error(f"Cache initialization failed: {exc}")
        _fallback_init(app)


def _fallback_init(app) -> None:
    """Provide a minimal in-memory cache if Flask-Caching is unavailable."""

    class _DictCache:
        def __init__(self) -> None:
            self._data: dict[str, tuple[Any, float | None]] = {}

        def get(self, key: str) -> Any:
            item = self._data.get(key)
            if not item:
                cache_monitor.record_cache_miss("memory")
                return None
            value, expiry = item
            if expiry is not None and time.time() > expiry:
                self._data.pop(key, None)
                cache_monitor.record_cache_miss("memory")
                return None
            if isinstance(value, weakref.ReferenceType):
                value = value()
                if value is None:
                    self._data.pop(key, None)
                    cache_monitor.record_cache_miss("memory")
                    return None
            cache_monitor.record_cache_hit("memory")
            return value

        def set(self, key: str, value: Any, timeout: int | None = None) -> None:
            expiry = time.time() + timeout if timeout else None
            try:
                self._data[key] = (
                    weakref.ref(value, lambda _, k=key: self._data.pop(k, None)),
                    expiry,
                )
            except TypeError:
                self._data[key] = (value, expiry)

        def delete(self, key: str) -> None:
            self._data.pop(key, None)

        def clear(self) -> None:
            self._data.clear()

    cache = _DictCache()
    ServiceRegistry.register("cache", cache)
    app.extensions["cache"] = cache


__all__ = ["get_cache", "init_app"]
