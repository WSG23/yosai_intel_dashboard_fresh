from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from yosai_intel_dashboard.src.core.intelligent_multilevel_cache import IntelligentMultiLevelCache
from yosai_intel_dashboard.src.infrastructure.cache.cache_manager import CacheConfig


@pytest.mark.asyncio
async def test_disk_promotion(tmp_path: Path):
    cfg = CacheConfig(timeout_seconds=10)
    cfg.disk_path = str(tmp_path)
    cache = IntelligentMultiLevelCache(cfg)
    await cache.start()
    await cache.set("a", "b")
    cache._memory.clear()
    assert await cache.get("a") == "b"
    assert "a" in cache._memory
    await cache.stop()


@pytest.mark.asyncio
async def test_expiration(tmp_path: Path):
    cfg = CacheConfig(timeout_seconds=1)
    cfg.disk_path = str(tmp_path)
    cache = IntelligentMultiLevelCache(cfg)
    await cache.start()
    await cache.set("k", "v", ttl=1)
    await asyncio.sleep(1.1)
    assert await cache.get("k") is None
    await cache.stop()


@pytest.mark.asyncio
async def test_cache_report(tmp_path: Path):
    cfg = CacheConfig(timeout_seconds=10)
    cfg.disk_path = str(tmp_path)
    cache = IntelligentMultiLevelCache(cfg)
    await cache.start()
    await cache.set("r", 1)
    report = cache.report()
    assert report["memory_entries"] == 1
    assert report["disk_entries"] == 1
    await cache.stop()


@pytest.mark.asyncio
async def test_invalidate_and_clear(tmp_path: Path):
    cfg = CacheConfig(timeout_seconds=10)
    cfg.disk_path = str(tmp_path)
    cache = IntelligentMultiLevelCache(cfg)
    await cache.start()
    await cache.set("x", "y")
    await cache.invalidate("x")
    assert await cache.get("x") is None
    await cache.set("x", "y")
    await cache.clear(level=1)
    assert "x" not in cache._memory
    await cache.clear()
    assert await cache.get("x") is None
    await cache.stop()


@pytest.mark.asyncio
async def test_demotion_moves_cold_entries(tmp_path: Path):
    cfg = CacheConfig(timeout_seconds=10)
    cfg.disk_path = str(tmp_path)
    cache = IntelligentMultiLevelCache(cfg)
    await cache.start()
    await cache.set("cold", "data", ttl=10)
    await asyncio.sleep(6)
    await cache.demote()
    assert "cold" not in cache._memory
    assert await cache.get("cold") == "data"
    assert "cold" not in cache._memory
    await cache.stop()
