from __future__ import annotations

"""Asynchronous cache manager with optional Redis backend."""

import asyncio
import json
import logging
import time
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, Optional

import redis.asyncio as redis

# from config.config import get_cache_config  # Moved to lazy import
from config.cache_config import CacheConfig

logger = logging.getLogger(__name__)


class AdvancedCacheManager:
    """Async cache manager using Redis with in-memory fallback."""

    def __init__(self, cache_config: CacheConfig) -> None:
        self.config = cache_config
        self.key_prefix = getattr(cache_config, "key_prefix", "yosai:")
        self.default_ttl = getattr(cache_config, "timeout_seconds", 300)
        self._redis: Optional[redis.Redis] = None
        self._memory: Dict[str, tuple[Any, Optional[float]]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    # ------------------------------------------------------------------
    async def start(self) -> None:
        """Initialize Redis connection."""
        if self._redis is None:
            self._redis = redis.Redis(
                host=getattr(self.config, "host", "localhost"),
                port=getattr(self.config, "port", 6379),
                db=getattr(self.config, "database", 0),
            )
        try:
            await self._redis.ping()
            logger.info("Advanced cache manager connected to Redis")
        except Exception as exc:  # pragma: no cover - best effort
            logger.error(f"Failed to connect to Redis: {exc}")
            self._redis = None

    # ------------------------------------------------------------------
    async def stop(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            try:
                await self._redis.close()
            finally:
                self._redis = None
        self._memory.clear()
        self._locks.clear()

    # ------------------------------------------------------------------
    def _make_key(self, key: str) -> str:
        return f"{self.key_prefix}{key}"

    # ------------------------------------------------------------------
    async def get(self, key: str) -> Optional[Any]:
        full_key = self._make_key(key)
        if self._redis is not None:
            try:
                data = await self._redis.get(full_key)
                return json.loads(data.decode("utf-8")) if data is not None else None
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning(f"Redis GET failed for {full_key}: {exc}")
                return None
        # Fallback to memory
        if key not in self._memory:
            return None
        value, expiry = self._memory[key]
        if expiry is not None and time.time() > expiry:
            del self._memory[key]
            return None
        return value

    # ------------------------------------------------------------------
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        full_key = self._make_key(key)
        expire = ttl if ttl is not None else self.default_ttl
        if self._redis is not None:
            try:
                payload = json.dumps(value).encode("utf-8")
                if expire:
                    await self._redis.setex(full_key, expire, payload)
                else:
                    await self._redis.set(full_key, payload)
                return
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning(f"Redis SET failed for {full_key}: {exc}")
        # Fallback to memory
        expiry = time.time() + expire if expire else None
        self._memory[key] = (value, expiry)

    # ------------------------------------------------------------------
    async def delete(self, key: str) -> bool:
        full_key = self._make_key(key)
        if self._redis is not None:
            try:
                removed = await self._redis.delete(full_key)
                if removed:
                    return True
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning(f"Redis DEL failed for {full_key}: {exc}")
        return self._memory.pop(key, None) is not None

    # ------------------------------------------------------------------
    async def clear(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.flushdb()
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning(f"Redis FLUSHDB failed: {exc}")
        self._memory.clear()

    # ------------------------------------------------------------------
    def get_lock(self, key: str, timeout: int = 10):
        """Return an async context manager lock for the key."""
        if self._redis is not None:
            return self._redis.lock(self._make_key(f"lock:{key}"), timeout=timeout)
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock


# ----------------------------------------------------------------------


def cache_with_lock(
    manager: AdvancedCacheManager,
    ttl: Optional[int] = None,
    key_func: Optional[Callable[..., str]] = None,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Cache async function results with a per-key lock."""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = (
                key_func(*args, **kwargs)
                if key_func
                else f"{func.__module__}.{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            )
            async with manager.get_lock(cache_key):
                cached = await manager.get(cache_key)
                if cached is not None:
                    return cached
                result = await func(*args, **kwargs)
                await manager.set(cache_key, result, ttl)
                return result

        return wrapper

    return decorator


# ----------------------------------------------------------------------


async def create_advanced_cache_manager() -> AdvancedCacheManager:
    """Initialize :class:`AdvancedCacheManager` using application config."""
    from config.config import get_cache_config  # Lazy import

    cfg = get_cache_config()
    manager = AdvancedCacheManager(cfg)
    await manager.start()
    return manager


__all__ = [
    "AdvancedCacheManager",
    "cache_with_lock",
    "create_advanced_cache_manager",
]
