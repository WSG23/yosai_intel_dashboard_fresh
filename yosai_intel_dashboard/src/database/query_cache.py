from __future__ import annotations

"""Simple query result cache backed by Redis."""

import asyncio
import os
from typing import Any, Optional

from yosai_intel_dashboard.src.core.cache_manager import CacheConfig, RedisCacheManager


class QueryCache:
    """Cache wrapper for database query results."""

    def __init__(
        self,
        cache_manager: Optional[RedisCacheManager] = None,
        *,
        host: Optional[str] = None,
        port: Optional[int] = None,
        ttl: Optional[int] = None,
    ) -> None:
        cfg = CacheConfig()
        if host is not None:
            cfg.host = host
        if port is not None:
            cfg.port = port
        self.ttl = ttl if ttl is not None else int(os.getenv("QUERY_CACHE_TTL", cfg.timeout_seconds))
        self.cache = cache_manager or RedisCacheManager(cfg)
        asyncio.run(self.cache.start())

    def get(self, key: str):
        """Return cached value for ``key`` or ``None``."""
        return asyncio.run(self.cache.get(key))

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store ``value`` under ``key`` for ``ttl`` seconds."""
        asyncio.run(self.cache.set(key, value, ttl or self.ttl))

    def clear(self) -> None:
        """Remove all cache entries."""
        asyncio.run(self.cache.clear())

    def stop(self) -> None:
        """Release cache resources."""
        asyncio.run(self.cache.stop())


__all__ = ["QueryCache"]
