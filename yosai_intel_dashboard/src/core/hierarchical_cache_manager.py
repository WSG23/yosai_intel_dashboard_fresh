from __future__ import annotations

"""Simple hierarchical cache with three levels and basic metrics."""

import asyncio
import inspect
import logging
import os
import time
import weakref
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .base_model import BaseModel


@dataclass
class HierarchicalCacheConfig:
    """Configuration for :class:`HierarchicalCacheManager`.

    Values are loaded from environment variables with sensible defaults.
    """

    type: str = "hierarchical"
    l1_size: int = int(os.getenv("CACHE_L1_SIZE", "1024"))
    l2_host: str = os.getenv("CACHE_L2_HOST", "localhost")
    l2_port: int = int(os.getenv("CACHE_L2_PORT", "6379"))
    l2_ttl: int = int(os.getenv("CACHE_L2_TTL", "300"))
    l3_path: str = os.getenv("CACHE_L3_PATH", "/tmp/yosai_cache.db")
    l3_ttl: int = int(os.getenv("CACHE_L3_TTL", "3600"))


class HierarchicalCacheManager(BaseModel):
    """Manage a three-level in-memory cache and record basic stats."""


    def __init__(
        self,
        config: HierarchicalCacheConfig | None = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
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
                if isinstance(value, weakref.ReferenceType):
                    value = value()
                    if value is None:
                        self._level1.pop(key, None)
                    else:
                        return value
                else:
                    return value
            else:
                del self._level1[key]
        item = self._level2.get(key)
        if item is not None:
            value, expiry = item
            if expiry is None or time.time() <= expiry:
                if isinstance(value, weakref.ReferenceType):
                    value = value()
                    if value is None:
                        self._level2.pop(key, None)
                    else:
                        return value
                else:
                    return value
            else:
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

        def _remove(_ref, *, k=key, lvl=level) -> None:
            cache = self._level1 if lvl == 1 else self._level2
            cache.pop(k, None)

        try:
            stored: Any = weakref.ref(value, _remove)
        except TypeError:
            stored = value

        if level == 1:
            self._level1[key] = (stored, expiry)
        else:
            self._level2[key] = (stored, expiry)

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
        self._level3.clear()

    def evict(self, key: str, *, level: int | None = None) -> None:
        if level is None:
            for lvl in (1, 2, 3):
                self.evict(key, level=lvl)
            return
        cache = {1: self._level1, 2: self._level2, 3: self._level3}[level]
        if key in cache:
            del cache[key]
            self._evictions[f"l{level}"] += 1

    def stats(self) -> Dict[str, Dict[str, int]]:
        return {
            "l1": {
                "hits": self._hits["l1"],
                "misses": self._misses["l1"],
                "evictions": self._evictions["l1"],
            },
            "l2": {
                "hits": self._hits["l2"],
                "misses": self._misses["l2"],
                "evictions": self._evictions["l2"],
            },
            "l3": {
                "hits": self._hits["l3"],
                "misses": self._misses["l3"],
                "evictions": self._evictions["l3"],
            },
        }


    async def warm(self, keys: list[str], loader: Callable[[str], Any]) -> None:
        """Pre-populate all cache tiers for the specified *keys*.

        The *loader* callable is used to retrieve the value for each key. It can
        be either a synchronous function or an async coroutine. Values are stored
        in both cache levels.
        """

        async def _populate(key: str) -> None:
            if inspect.iscoroutinefunction(loader):
                value = await loader(key)
            else:
                value = await asyncio.to_thread(loader, key)
            await self.set(key, value, level=1)
            await self.set(key, value, level=2)

        await asyncio.gather(*(_populate(k) for k in keys))

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


__all__ = ["HierarchicalCacheConfig", "HierarchicalCacheManager"]
