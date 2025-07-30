import asyncio

from core.cache_warmer import IntelligentCacheWarmer, UsagePatternAnalyzer
from core.hierarchical_cache_manager import HierarchicalCacheManager


def _loader(key: str) -> str:
    return f"value-{key}"


def test_predicted_keys_cached(async_runner):
    cache = HierarchicalCacheManager()
    warmer = IntelligentCacheWarmer(cache, _loader)

    # record some usage patterns
    warmer.record_usage("a")
    warmer.record_usage("b")
    warmer.record_usage("a")

    async_runner(warmer.warm())

    assert cache.get("a") == "value-a"
    assert cache.get("b") == "value-b"
