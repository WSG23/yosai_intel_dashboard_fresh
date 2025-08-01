"""Simple cache manager implementations."""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from yosai_intel_dashboard.src.core.intelligent_multilevel_cache import IntelligentMultiLevelCache

from .constants import DEFAULT_CACHE_HOST, DEFAULT_CACHE_PORT


@dataclass
class CacheConfig:
    """Cache configuration"""

    type: str = "memory"
    host: str = DEFAULT_CACHE_HOST
    port: int = DEFAULT_CACHE_PORT
    disk_path: str = "/tmp/yosai_cache"


logger = logging.getLogger(__name__)


class MemoryCacheManager:
    """In-memory cache manager."""

    def __init__(self, cache_config: CacheConfig):
        self.config = cache_config
        self._cache: Dict[str, Any] = {}
        self.key_prefix = getattr(cache_config, "key_prefix", "yosai:")
        self.timeout_seconds = getattr(cache_config, "timeout_seconds", 300)
        self.max_memory_mb = getattr(cache_config, "max_memory_mb", 100)

    def get(self, key: str) -> Any:
        return self._cache.get(f"{self.key_prefix}{key}")

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        self._cache[f"{self.key_prefix}{key}"] = value

    def clear(self) -> None:
        self._cache.clear()

    def start(self) -> None:
        logger.info("Memory cache manager started")

    def stop(self) -> None:
        self.clear()


class RedisCacheManager:
    """Placeholder Redis cache manager using memory fallback."""

    def __init__(self, cache_config: CacheConfig):
        self.config = cache_config
        self._fallback = MemoryCacheManager(cache_config)
        logger.info("Redis cache manager initialized (using memory fallback)")

    def get(self, key: str) -> Any:
        return self._fallback.get(key)

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        self._fallback.set(key, value, timeout)

    def clear(self) -> None:
        self._fallback.clear()

    def start(self) -> None:
        logger.info("Redis cache manager started")

    def stop(self) -> None:
        pass


def from_environment() -> CacheConfig:
    """Create ``CacheConfig`` from environment variables."""
    return CacheConfig(
        type=os.getenv("CACHE_TYPE", "memory"),
        host=os.getenv("CACHE_HOST", DEFAULT_CACHE_HOST),
        port=int(os.getenv("CACHE_PORT", DEFAULT_CACHE_PORT)),
        disk_path=os.getenv("CACHE_DISK_PATH", "/tmp/yosai_cache"),
    )


def get_cache_manager() -> Any:
    """Get cache manager instance using environment configuration."""
    cfg = from_environment()
    if cfg.type == "redis":
        return RedisCacheManager(cfg)
    if cfg.type == "intelligent":
        return IntelligentMultiLevelCache(cfg)
    return MemoryCacheManager(cfg)


__all__ = [
    "MemoryCacheManager",
    "RedisCacheManager",
    "IntelligentMultiLevelCache",
    "CacheConfig",
    "from_environment",
    "get_cache_manager",
]
