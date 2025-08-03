from __future__ import annotations

import asyncio
import pytest

from yosai_intel_dashboard.src.core.cache_warmer import IntelligentCacheWarmer, UsagePatternAnalyzer
from yosai_intel_dashboard.src.core.hierarchical_cache_manager import HierarchicalCacheManager


@pytest.fixture
def async_runner():
    return asyncio.run


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

    assert async_runner(cache.get("a")) == "value-a"
    assert async_runner(cache.get("b")) == "value-b"


def test_warm_populates_keys(async_runner):
    cache = HierarchicalCacheManager()
    async_runner(cache.warm(["x", "y"], _loader))
    assert async_runner(cache.get("x")) == "value-x"
    assert async_runner(cache.get("y")) == "value-y"


def test_warm_from_file(async_runner, tmp_path):
    cache = HierarchicalCacheManager()
    warmer = IntelligentCacheWarmer(cache, _loader)
    warmer.record_usage("a")
    warmer.record_usage("b")
    warmer.record_usage("a")
    stats = tmp_path / "stats.json"
    warmer.save_stats(stats)

    new_cache = HierarchicalCacheManager()
    new_warmer = IntelligentCacheWarmer(new_cache, _loader)
    async_runner(new_warmer.warm_from_file(stats))

    assert async_runner(new_cache.get("a")) == "value-a"
    assert async_runner(new_cache.get("b")) == "value-b"
