import asyncio
from pathlib import Path

import pytest

from yosai_intel_dashboard.src.infrastructure.config.base import CacheConfig
from core.intelligent_multilevel_cache import IntelligentMultiLevelCache


@pytest.mark.asyncio
async def test_disk_promotion(tmp_path: Path):
    cfg = CacheConfig(timeout_seconds=10, disk_path=str(tmp_path))
    cache = IntelligentMultiLevelCache(cfg)
    await cache.start()
    await cache.set("a", "b")
    cache._memory.clear()
    assert await cache.get("a") == "b"
    assert "a" in cache._memory
    await cache.stop()


@pytest.mark.asyncio
async def test_expiration(tmp_path: Path):
    cfg = CacheConfig(timeout_seconds=1, disk_path=str(tmp_path))
    cache = IntelligentMultiLevelCache(cfg)
    await cache.start()
    await cache.set("k", "v", ttl=1)
    await asyncio.sleep(1.1)
    assert await cache.get("k") is None
    await cache.stop()


@pytest.mark.asyncio
async def test_cache_report(tmp_path: Path):
    cfg = CacheConfig(timeout_seconds=10, disk_path=str(tmp_path))
    cache = IntelligentMultiLevelCache(cfg)
    await cache.start()
    await cache.set("r", 1)
    report = cache.report()
    assert report["memory_entries"] == 1
    assert report["disk_entries"] == 1
    await cache.stop()
