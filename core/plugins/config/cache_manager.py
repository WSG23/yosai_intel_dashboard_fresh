"""Enhanced cache managers implementing the interface"""

import logging
import time
from typing import Optional, Any, Dict
import pickle

import redis
from dataclasses import dataclass
from .interfaces import ICacheManager

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with expiration"""

    value: Any
    created_at: float
    ttl: Optional[float] = None

    @property
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


class MemoryCacheManager(ICacheManager):
    """Memory-based cache manager"""

    def __init__(self, cache_config):
        self.config = cache_config
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = getattr(cache_config, "timeout_seconds", 300)
        self._started = False

    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_expired:
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in memory cache"""
        cache_ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(
            value=value, created_at=time.time(), ttl=cache_ttl
        )

    def delete(self, key: str) -> bool:
        """Delete key from memory cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all memory cache entries"""
        self._cache.clear()

    def start(self) -> None:
        """Start memory cache"""
        self._started = True
        logger.info("Memory cache manager started")

    def stop(self) -> None:
        """Stop memory cache"""
        self.clear()
        self._started = False
        logger.info("Memory cache manager stopped")


class RedisCacheManager(ICacheManager):
    """Redis-based cache manager"""

    def __init__(self, cache_config):
        self.config = cache_config
        self.redis_client: Optional[redis.Redis] = None
        self._started = False

    def _client(self) -> redis.Redis:
        if self.redis_client is None:
            self.redis_client = redis.Redis(
                host=getattr(self.config, "host", "localhost"),
                port=getattr(self.config, "port", 6379),
                db=getattr(self.config, "db", 0),
            )
        return self.redis_client

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self._started:
            return None
        try:
            data = self._client().get(key)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception as e:
            logger.warning(f"Redis GET failed: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in Redis cache"""
        if not self._started:
            return
        try:
            data = pickle.dumps(value)
            expire = ttl or getattr(self.config, "ttl", None)
            if expire:
                self._client().setex(key, expire, data)
            else:
                self._client().set(key, data)
        except Exception as e:
            logger.warning(f"Redis SET failed: {e}")

    def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        if not self._started:
            return False
        try:
            return self._client().delete(key) > 0
        except Exception as e:
            logger.warning(f"Redis DEL failed: {e}")
            return False

    def clear(self) -> None:
        """Clear all Redis cache entries"""
        if not self._started:
            return
        try:
            self._client().flushdb()
        except Exception as e:
            logger.warning(f"Redis FLUSHDB failed: {e}")

    def start(self) -> None:
        """Start Redis cache connection"""
        try:
            self._client().ping()
            self._started = True
            logger.info("Redis cache manager started")
        except Exception as e:
            logger.error(f"Failed to start Redis cache manager: {e}")
            raise

    def stop(self) -> None:
        """Stop Redis cache connection"""
        if self.redis_client is not None:
            try:
                self.redis_client.close()
            except Exception:
                pass
        self.redis_client = None
        self._started = False
        logger.info("Redis cache manager stopped")


__all__ = ["MemoryCacheManager", "RedisCacheManager", "CacheEntry"]
