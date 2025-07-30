from __future__ import annotations

"""Caching helpers for analytics storage."""

from core.cache_manager import CacheConfig, InMemoryCacheManager, cache_with_lock

_cache_manager = InMemoryCacheManager(CacheConfig())


def cached(ttl: int):
    return cache_with_lock(_cache_manager, ttl=ttl)


__all__ = ["cached", "_cache_manager"]
