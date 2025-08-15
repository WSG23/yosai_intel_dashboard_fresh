"""Simple cache interface used throughout the application."""

from __future__ import annotations

import logging
import time
import weakref
from typing import Any

from .registry import ServiceRegistry
from .performance import cache_monitor

logger = logging.getLogger(__name__)


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


def get_cache() -> _DictCache:
    """Return the shared cache instance from the service registry."""

    cache = ServiceRegistry.get("cache")
    if cache is None:
        cache = _DictCache()
        ServiceRegistry.register("cache", cache)
    return cache


def init_app(app) -> None:
    """Attach the cache instance to the given FastAPI app."""
    cache = get_cache()
    if hasattr(app, "state"):
        app.state.cache = cache


    # For compatibility with legacy code expecting an extensions dict
    if hasattr(app, "extensions"):
        app.extensions["cache"] = cache


__all__ = ["get_cache", "init_app"]
