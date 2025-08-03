"""Caching implementations for Yosai Intel Dashboard."""

from .cache_manager import (
    CacheConfig,
    InMemoryCacheManager,
    RedisCacheManager,
    cache_with_lock,
)

try:  # optional redis helpers
    from .redis_client import get_metrics_client, get_session_client, redis_client
except Exception:  # pragma: no cover - redis optional
    get_metrics_client = get_session_client = redis_client = None

__all__ = [
    "CacheConfig",
    "InMemoryCacheManager",
    "RedisCacheManager",
    "cache_with_lock",
    "get_session_client",
    "get_metrics_client",
    "redis_client",
]
