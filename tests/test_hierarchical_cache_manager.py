from __future__ import annotations

import pytest

from core.cache_manager import cache_with_lock
from core.hierarchical_cache_manager import HierarchicalCacheManager
from yosai_intel_dashboard.src.core.performance import cache_monitor


@pytest.mark.asyncio
async def test_cache_with_lock_hierarchical_async():
    manager = HierarchicalCacheManager()
    cache_monitor.cache_stats.clear()
    calls = {"n": 0}

    @cache_with_lock(manager, ttl=1, name="asyncfunc")
    async def compute(x):
        calls["n"] += 1
        return x * 2

    assert await compute(3) == 6
    assert await compute(3) == 6
    assert calls["n"] == 1

    stats = cache_monitor.cache_stats["asyncfunc"]
    assert stats["hits"] == 1
    assert stats["misses"] == 1


def test_cache_with_lock_hierarchical_sync():
    manager = HierarchicalCacheManager()
    cache_monitor.cache_stats.clear()
    calls = {"n": 0}

    @cache_with_lock(manager, ttl=1, name="syncfunc")
    def compute(x):
        calls["n"] += 1
        return x + 5

    assert compute(1) == 6
    assert compute(1) == 6
    assert calls["n"] == 1

    stats = cache_monitor.cache_stats["syncfunc"]
    assert stats["hits"] == 1
    assert stats["misses"] == 1


def test_sync_helpers():
    manager = HierarchicalCacheManager()
    manager.set_sync("key", "value")
    assert manager.get_sync("key") == "value"
    assert manager.delete_sync("key") is True
    assert manager.get_sync("key") is None

