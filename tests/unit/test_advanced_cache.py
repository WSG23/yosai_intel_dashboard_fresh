import pytest

from yosai_intel_dashboard.src.core.cache_manager import CacheConfig, InMemoryCacheManager, cache_with_lock


@pytest.mark.asyncio
async def test_cache_with_lock_basic():
    manager = InMemoryCacheManager(CacheConfig(timeout_seconds=1))
    await manager.start()

    calls = {"n": 0}

    @cache_with_lock(manager, ttl=1)
    async def compute(val: int) -> int:
        calls["n"] += 1
        return val * 2

    assert await compute(2) == 4
    assert await compute(2) == 4
    assert calls["n"] == 1

    await manager.stop()
