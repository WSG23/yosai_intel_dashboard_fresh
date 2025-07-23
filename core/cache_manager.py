from __future__ import annotations

"""Unified asynchronous cache manager with pluggable backends."""

import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for :class:`CacheManager`."""

    host: str = os.getenv("CACHE_HOST", "localhost")
    port: int = int(os.getenv("CACHE_PORT", "6379"))
    db: int = int(os.getenv("CACHE_DB", "0"))
    key_prefix: str = os.getenv("CACHE_PREFIX", "yosai:")
    timeout_seconds: int = int(os.getenv("CACHE_TTL", "300"))


class CacheManager(ABC):
    """Abstract cache manager interface."""

    def __init__(self, config: CacheConfig) -> None:
        self.config = config

    # ------------------------------------------------------------------
    @abstractmethod
    async def start(self) -> None:
        """Initialize any backend resources."""

    # ------------------------------------------------------------------
    @abstractmethod
    async def stop(self) -> None:
        """Release backend resources."""

    # ------------------------------------------------------------------
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Return cached value for ``key`` or ``None``."""

    # ------------------------------------------------------------------
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store ``value`` under ``key`` for ``ttl`` seconds."""

    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete ``key`` and return ``True`` if present."""

    # ------------------------------------------------------------------
    @abstractmethod
    async def clear(self) -> None:
        """Remove all cache entries."""

    # ------------------------------------------------------------------
    @abstractmethod
    def get_lock(self, key: str, timeout: int = 10) -> asyncio.Lock:
        """Return an async lock for ``key``."""

    # ------------------------------------------------------------------
    def _full_key(self, key: str) -> str:
        return f"{self.config.key_prefix}{key}"


class InMemoryCacheManager(CacheManager):
    """Simple in-memory cache manager."""

    def __init__(self, config: CacheConfig) -> None:
        super().__init__(config)
        self._cache: Dict[str, tuple[Any, Optional[float]]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def start(self) -> None:  # pragma: no cover - nothing to do
        pass

    async def stop(self) -> None:
        self._cache.clear()
        self._locks.clear()

    async def get(self, key: str) -> Optional[Any]:
        item = self._cache.get(key)
        if not item:
            return None
        value, expiry = item
        if expiry is not None and time.time() > expiry:
            del self._cache[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expiry = time.time() + ttl if ttl else None
        self._cache[key] = (value, expiry)

    async def delete(self, key: str) -> bool:
        return self._cache.pop(key, None) is not None

    async def clear(self) -> None:
        self._cache.clear()

    def get_lock(self, key: str, timeout: int = 10) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock


class RedisCacheManager(CacheManager):
    """Redis-backed cache manager with in-memory fallback."""

    def __init__(self, config: CacheConfig) -> None:
        super().__init__(config)
        self._redis: Optional[redis.Redis] = None
        self._fallback = InMemoryCacheManager(config)

    async def start(self) -> None:
        if self._redis is None:
            self._redis = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
            )
        try:
            await self._redis.ping()
        except Exception as exc:  # pragma: no cover - fallback
            logger.error("Redis unavailable: %s", exc)
            self._redis = None
        await self._fallback.start()

    async def stop(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.close()
            finally:
                self._redis = None
        await self._fallback.stop()

    async def get(self, key: str) -> Optional[Any]:
        if self._redis is not None:
            try:
                data = await self._redis.get(self._full_key(key))
                if data is not None:
                    return json.loads(data.decode("utf-8"))
            except Exception as exc:  # pragma: no cover - fallback
                logger.warning("Redis GET failed for %s: %s", key, exc)
        return await self._fallback.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expire = ttl if ttl is not None else self.config.timeout_seconds
        payload = json.dumps(value).encode("utf-8")
        if self._redis is not None:
            try:
                if expire:
                    await self._redis.setex(self._full_key(key), expire, payload)
                else:
                    await self._redis.set(self._full_key(key), payload)
                return
            except Exception as exc:  # pragma: no cover - fallback
                logger.warning("Redis SET failed for %s: %s", key, exc)
        await self._fallback.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        if self._redis is not None:
            try:
                removed = await self._redis.delete(self._full_key(key))
                if removed:
                    return True
            except Exception as exc:  # pragma: no cover - fallback
                logger.warning("Redis DEL failed for %s: %s", key, exc)
        return await self._fallback.delete(key)

    async def clear(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.flushdb()
            except Exception as exc:  # pragma: no cover - fallback
                logger.warning("Redis FLUSHDB failed: %s", exc)
        await self._fallback.clear()

    def get_lock(self, key: str, timeout: int = 10):
        if self._redis is not None:
            return self._redis.lock(self._full_key(f"lock:{key}"), timeout=timeout)
        return self._fallback.get_lock(key, timeout)


# ----------------------------------------------------------------------

def cache_with_lock(
    manager: CacheManager,
    ttl: Optional[int] = None,
    key_func: Optional[Callable[..., str]] = None,
    name: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Cache results of ``func`` using ``manager`` and a per-key lock."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        is_async = asyncio.iscoroutinefunction(func)
        env_var = f"CACHE_TTL_{(name or func.__name__).upper()}"

        async def _execute(*args: Any, **kwargs: Any) -> Any:
            cache_key = (
                key_func(*args, **kwargs)
                if key_func
                else f"{func.__module__}.{func.__name__}:{hash(str(args)+str(sorted(kwargs.items())))}"
            )
            async with manager.get_lock(cache_key):
                cached = await manager.get(cache_key)
                if cached is not None:
                    return cached
                result = await func(*args, **kwargs) if is_async else func(*args, **kwargs)
                override = os.getenv(env_var)
                effective_ttl = int(override) if override and override.isdigit() else ttl
                await manager.set(cache_key, result, effective_ttl)
                return result

        if is_async:
            return _execute

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return asyncio.run(_execute(*args, **kwargs))

        return wrapper

    return decorator


__all__ = [
    "CacheConfig",
    "CacheManager",
    "InMemoryCacheManager",
    "RedisCacheManager",
    "cache_with_lock",
]
