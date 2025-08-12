import sys
import types

import pytest

perf_stub = types.ModuleType("yosai_intel_dashboard.src.core.performance")
perf_stub.cache_monitor = types.SimpleNamespace(
    record_cache_hit=lambda *a, **k: None,
    record_cache_miss=lambda *a, **k: None,
)
sys.modules["yosai_intel_dashboard.src.core.performance"] = perf_stub

from yosai_intel_dashboard.src.infrastructure.cache.cache_manager import (
    CacheConfig,
    InMemoryCacheManager,
)


@pytest.mark.asyncio
@pytest.mark.performance
async def test_lru_eviction() -> None:
    cfg = CacheConfig(timeout_seconds=10, max_items=2)
    manager = InMemoryCacheManager(cfg)
    await manager.start()

    await manager.set("a", 1)
    await manager.set("b", 2)
    assert await manager.get("a") == 1

    await manager.set("c", 3)  # should evict key 'b'

    assert await manager.get("b") is None
    assert await manager.get("a") == 1
    assert await manager.get("c") == 3

    await manager.stop()
