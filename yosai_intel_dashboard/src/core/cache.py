"""Simple cache interface used throughout the application."""

from __future__ import annotations

import logging
from typing import Any

from flask_caching import Cache

logger = logging.getLogger(__name__)

cache = Cache()


def init_app(app) -> None:
    """Initialize the cache with the given Flask app."""
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
            self._data: dict[str, Any] = {}

        def get(self, key: str) -> Any:
            return self._data.get(key)

        def set(self, key: str, value: Any, timeout: int | None = None) -> None:
            self._data[key] = value

        def delete(self, key: str) -> None:
            self._data.pop(key, None)

        def clear(self) -> None:
            self._data.clear()

    global cache
    cache = _DictCache()
    app.extensions["cache"] = cache


__all__ = ["cache", "init_app"]
