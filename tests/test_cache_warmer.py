from __future__ import annotations

import asyncio

from yosai_intel_dashboard.src.core.cache_warmer import IntelligentCacheWarmer, UsagePatternAnalyzer
from yosai_intel_dashboard.src.core.hierarchical_cache_manager import HierarchicalCacheManager


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


def test_warm_populates_keys(async_runner):
    cache = HierarchicalCacheManager()
    async_runner(cache.warm(["x", "y"], _loader))
    assert cache.get("x") == "value-x"
    assert cache.get("y") == "value-y"
