from __future__ import annotations

"""Simple hierarchical cache with two levels."""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from .base_model import BaseModel


class HierarchicalCacheManager(BaseModel):
    """Manage a two-level in-memory cache."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create the cache manager with optional config, DB and logger."""
        super().__init__(config, db, logger)
        self._level1: Dict[str, tuple[Any, Optional[float]]] = {}
        self._level2: Dict[str, tuple[Any, Optional[float]]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache, checking level1 then level2."""
        item = self._level1.get(key)
        if item is not None:
            value, expiry = item
            if expiry is None or time.time() <= expiry:
                return value
            del self._level1[key]
        item = self._level2.get(key)
        if item is not None:
            value, expiry = item
            if expiry is None or time.time() <= expiry:
                return value
            del self._level2[key]
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        *,
        level: int = 1,
    ) -> None:
        """Store ``value`` at the specified cache ``level``."""
        expiry = time.time() + ttl if ttl else None
        if level == 1:
            self._level1[key] = (value, expiry)
        else:
            self._level2[key] = (value, expiry)

    async def delete(self, key: str) -> bool:
        """Delete ``key`` from any level and return if removed."""
        removed = False
        if self._level1.pop(key, None) is not None:
            removed = True
        if self._level2.pop(key, None) is not None:
            removed = True
        return removed

    async def clear(self) -> None:
        """Clear all cache levels."""
        self._level1.clear()
        self._level2.clear()

    def get_lock(self, key: str, timeout: int = 10) -> asyncio.Lock:
        """Return an asyncio lock for ``key``."""
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    # ------------------------------------------------------------------
    # Synchronous helpers
    def get_sync(self, key: str) -> Optional[Any]:
        """Synchronous wrapper around :meth:`get`."""
        return asyncio.run(self.get(key))

    def set_sync(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        *,
        level: int = 1,
    ) -> None:
        """Synchronous wrapper around :meth:`set`."""
        asyncio.run(self.set(key, value, ttl, level=level))

    def delete_sync(self, key: str) -> bool:
        """Synchronous wrapper around :meth:`delete`."""
        return asyncio.run(self.delete(key))


__all__ = ["HierarchicalCacheManager"]
