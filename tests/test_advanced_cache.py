import pytest

from core.advanced_cache import AdvancedCacheManager, cache_with_lock
from config.base import CacheConfig


@pytest.mark.asyncio
async def test_cache_with_lock_basic():
    manager = AdvancedCacheManager(CacheConfig(timeout_seconds=1))
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
