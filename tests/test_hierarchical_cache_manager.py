from core.hierarchical_cache_manager import HierarchicalCacheManager
from core.performance import cache_monitor


def test_stats_and_monitoring():
    cache = HierarchicalCacheManager()
    cache_monitor.register_cache("hc", cache)

    cache.get("missing")
    cache.set("a", 1, level=1)
    cache.get("a")
    cache.set("b", 2, level=2)
    cache.get("b")
    cache.set("c", 3, level=3)
    cache.get("c")
    cache.evict("a", level=1)
    cache.clear()

    stats = cache.stats()
    assert stats["l1"]["hits"] == 1
    assert stats["l1"]["misses"] == 3
    assert stats["l1"]["evictions"] == 1
    assert stats["l2"]["hits"] == 1
    assert stats["l2"]["misses"] == 2
    assert stats["l2"]["evictions"] == 1
    assert stats["l3"]["hits"] == 1
    assert stats["l3"]["misses"] == 1
    assert stats["l3"]["evictions"] == 1

    all_stats = cache_monitor.get_all_cache_stats()
    assert "hc" in all_stats
    assert all_stats["hc"] == stats

    cache_monitor._caches.pop("hc", None)
