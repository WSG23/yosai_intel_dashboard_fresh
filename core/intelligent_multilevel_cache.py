from __future__ import annotations

"""Async multi-level cache with memory, Redis and disk layers."""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional

import redis.asyncio as redis

from config.base import CacheConfig

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache storage tiers."""

    L1 = "memory"
    L2 = "redis"
    L3 = "disk"


@dataclass
class CacheEntry:
    """Value stored in cache."""

    value: Any
    expiry: Optional[float]
    level: CacheLevel


class IntelligentMultiLevelCache:
    """Coordinate L1 memory, L2 Redis and L3 disk caches."""

    def __init__(self, cache_config: CacheConfig) -> None:
        self.config = cache_config
        self.key_prefix = getattr(cache_config, "key_prefix", "yosai:")
        self.default_ttl = getattr(cache_config, "timeout_seconds", 300)
        self.disk_path = Path(getattr(cache_config, "disk_path", "/tmp/yosai_cache"))
        self.memory_limit = 1000
        self._redis: Optional[redis.Redis] = None
        self._memory: Dict[str, CacheEntry] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    # ------------------------------------------------------------------
    async def start(self) -> None:
        """Create Redis connection and ensure disk directory exists."""
        self.disk_path.mkdir(parents=True, exist_ok=True)
        if self._redis is None:
            self._redis = redis.Redis(
                host=getattr(self.config, "host", "localhost"),
                port=getattr(self.config, "port", 6379),
                db=getattr(self.config, "database", 0),
            )
        try:
            await self._redis.ping()
            logger.info("Intelligent cache connected to Redis")
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Redis unavailable: %s", exc)
            self._redis = None

    # ------------------------------------------------------------------
    async def stop(self) -> None:
        """Close Redis connection and clear memory."""
        if self._redis is not None:
            try:
                await self._redis.close()
            finally:
                self._redis = None
        self._memory.clear()
        self._locks.clear()

    # ------------------------------------------------------------------
    def _full_key(self, key: str) -> str:
        return f"{self.key_prefix}{key}"

    # ------------------------------------------------------------------
    def _record_memory(self, key: str, value: Any, expiry: Optional[float]) -> None:
        self._memory[key] = CacheEntry(value=value, expiry=expiry, level=CacheLevel.L1)
        if len(self._memory) > self.memory_limit:
            oldest = min(self._memory, key=lambda k: self._memory[k].expiry or 0)
            del self._memory[oldest]

    # ------------------------------------------------------------------
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value in all cache layers."""
        expire = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + expire if expire else None
        self._record_memory(key, value, expiry)
        data = json.dumps({"value": value, "expiry": expiry}).encode("utf-8")
        if self._redis is not None:
            try:
                if expire:
                    await self._redis.setex(self._full_key(key), expire, data)
                else:
                    await self._redis.set(self._full_key(key), data)
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("Redis SET failed for %s: %s", key, exc)
        try:
            (self.disk_path / f"{self._full_key(key)}.json").write_bytes(data)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Disk write failed for %s: %s", key, exc)

    # ------------------------------------------------------------------
    async def get(
        self,
        key: str,
        loader: Optional[Callable[[], Awaitable[Any]]] = None,
        ttl: Optional[int] = None,
    ) -> Optional[Any]:
        """Retrieve value from caches, optionally using loader."""
        now = time.time()
        entry = self._memory.get(key)
        if entry:
            if entry.expiry and now > entry.expiry:
                del self._memory[key]
            else:
                return entry.value

        if self._redis is not None:
            try:
                raw = await self._redis.get(self._full_key(key))
                if raw:
                    obj = json.loads(raw.decode("utf-8"))
                    expiry = obj.get("expiry")
                    if expiry and now > expiry:
                        await self._redis.delete(self._full_key(key))
                    else:
                        self._record_memory(key, obj["value"], expiry)
                        return obj["value"]
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("Redis GET failed for %s: %s", key, exc)

        file = self.disk_path / f"{self._full_key(key)}.json"
        if file.exists():
            try:
                obj = json.loads(file.read_text())
                expiry = obj.get("expiry")
                if expiry and now > expiry:
                    file.unlink(missing_ok=True)
                else:
                    await self.set(key, obj["value"], ttl=int(expiry - now) if expiry else ttl)
                    return obj["value"]
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("Disk read failed for %s: %s", key, exc)

        if loader:
            value = await loader()
            await self.set(key, value, ttl)
            return value
        return None

    # ------------------------------------------------------------------
    def get_lock(self, key: str, timeout: int = 10):
        if self._redis is not None:
            return self._redis.lock(self._full_key(f"lock:{key}"), timeout=timeout)
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    # ------------------------------------------------------------------
    def report(self) -> Dict[str, Any]:
        """Return simple cache statistics."""
        disk_entries = len(list(self.disk_path.glob("*.json")))
        return {
            "memory_entries": len(self._memory),
            "disk_entries": disk_entries,
            "redis_enabled": self._redis is not None,
        }


async def create_intelligent_cache_manager() -> IntelligentMultiLevelCache:
    """Initialize cache manager from configuration."""
    from config.config import get_cache_config

    cfg = get_cache_config()
    manager = IntelligentMultiLevelCache(cfg)
    await manager.start()
    return manager


__all__ = [
    "IntelligentMultiLevelCache",
    "CacheLevel",
    "CacheEntry",
    "create_intelligent_cache_manager",
]
