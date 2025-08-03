"""Session store implementations.

This module provides two session storage backends used by the authentication
system:

* :class:`MemcachedSessionStore` – primary backend backed by Memcached. It
  supports key expiration (TTL) and relies on Memcached's built-in LRU
  eviction policy when memory is exhausted.
* :class:`InMemorySessionStore` – lightweight fallback used primarily for
  tests or environments where Memcached isn't available. It mimics the public
  interface of the Memcached store and enforces TTL purely in Python.

Both stores expose ``get``, ``set`` and ``delete`` methods. Values are stored
as JSON serialisable dictionaries in order to keep the implementation simple
and dependency free.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict, Optional

try:  # pragma: no cover - import guarded for environments without dependency
    from pymemcache.client.base import Client
except Exception:  # pragma: no cover - fallback if library missing at runtime
    Client = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class MemcachedSessionStore:
    """Memcached backed session storage.

    Parameters
    ----------
    host, port:
        Memcached server location. Defaults to the ``MEMCACHED_HOST`` and
        ``MEMCACHED_PORT`` environment variables (``localhost:11211`` if not
        set).
    ttl:
        Default time-to-live in seconds for stored sessions. Individual calls
        may override this value.
    """

    def __init__(self, host: str | None = None, port: int | None = None, ttl: int = 3600) -> None:
        host = host or os.getenv("MEMCACHED_HOST", "localhost")
        port = port or int(os.getenv("MEMCACHED_PORT", "11211"))
        self.ttl = ttl
        self._client: Optional[Client] = None
        if Client is not None:
            try:
                self._client = Client((host, port))
            except Exception as exc:  # pragma: no cover - network failure
                logger.warning("Failed to connect to memcached at %s:%s: %s", host, port, exc)

    # ------------------------------------------------------------------
    def get(self, key: str) -> Optional[Dict]:
        """Return stored value for ``key`` or ``None`` if missing/expired."""

        if self._client is None:
            return None
        try:
            data = self._client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as exc:  # pragma: no cover - memcached failure
            logger.warning("Memcached get failed for %s: %s", key, exc)
            return None

    # ------------------------------------------------------------------
    def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> None:
        """Store ``value`` under ``key`` for ``ttl`` seconds."""

        if self._client is None:
            return
        try:
            payload = json.dumps(value)
            expire = ttl if ttl is not None else self.ttl
            self._client.set(key, payload, expire=expire)
        except Exception as exc:  # pragma: no cover - memcached failure
            logger.warning("Memcached set failed for %s: %s", key, exc)

    # ------------------------------------------------------------------
    def delete(self, key: str) -> None:
        if self._client is None:
            return
        try:
            self._client.delete(key)
        except Exception:  # pragma: no cover - ignore delete errors
            pass

    # ------------------------------------------------------------------
    def clear(self) -> None:
        if self._client is None:
            return
        try:
            self._client.flush_all()
        except Exception as exc:  # pragma: no cover - memcached failure
            logger.warning("Memcached flush_all failed: %s", exc)


class InMemorySessionStore:
    """Simple in-memory session store with TTL.

    This implementation is intentionally minimal and used for unit tests where
    running a real Memcached server would be unnecessary. It mirrors the
    public API of :class:`MemcachedSessionStore`.
    """

    def __init__(self, ttl: int = 3600) -> None:
        self.ttl = ttl
        self._cache: Dict[str, tuple[Dict, float]] = {}

    def get(self, key: str) -> Optional[Dict]:
        item = self._cache.get(key)
        if not item:
            return None
        value, expiry = item
        if expiry and time.time() > expiry:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> None:
        expire = time.time() + (ttl if ttl is not None else self.ttl)
        self._cache[key] = (value, expire)

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()


__all__ = [
    "MemcachedSessionStore",
    "InMemorySessionStore",
]

