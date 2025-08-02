from __future__ import annotations

import asyncio
import time
import types
from pathlib import Path

import pytest

from yosai_intel_dashboard.src.core.cache_warmer import IntelligentCacheWarmer
from yosai_intel_dashboard.src.core.hierarchical_cache_manager import (
    HierarchicalCacheManager,
)
from yosai_intel_dashboard.src.core.intelligent_multilevel_cache import (
    IntelligentMultiLevelCache,
)
from yosai_intel_dashboard.src.infrastructure.cache.cache_manager import (
    CacheConfig,
    InMemoryCacheManager,
    cache_with_lock,
)


class AsyncFakeRedis:
    """Minimal in-memory Redis replacement with TTL support."""

    def __init__(self) -> None:
        self.store: dict[str, tuple[bytes, float | None]] = {}
        self.locks: dict[str, asyncio.Lock] = {}

    async def ping(self) -> bool:  # pragma: no cover - trivial
        return True

    async def close(self) -> None:  # pragma: no cover - trivial
        pass

    async def set(self, key: str, value: bytes) -> None:
        self.store[key] = (value, None)

    async def setex(self, key: str, ttl: int, value: bytes) -> None:
        self.store[key] = (value, time.time() + ttl)

    async def get(self, key: str) -> bytes | None:
        item = self.store.get(key)
        if not item:
            return None
        value, expiry = item
        if expiry and time.time() > expiry:
            del self.store[key]
            return None
        return value

    async def delete(self, key: str) -> int:
        return int(self.store.pop(key, None) is not None)

    def lock(self, key: str, timeout: int = 10) -> asyncio.Lock:  # pragma: no cover
        lock = self.locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self.locks[key] = lock
        return lock

    async def flushdb(self) -> None:
        self.store.clear()


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> AsyncFakeRedis:
    """Patch redis.asyncio.Redis to use an in-memory stub."""
    import yosai_intel_dashboard.src.core.intelligent_multilevel_cache as imc

    fake = AsyncFakeRedis()
    monkeypatch.setattr(
        imc,
        "redis",
        types.SimpleNamespace(Redis=lambda *a, **k: fake),
    )
    return fake


def test_promotion_and_eviction(
    tmp_path: Path, fake_redis: AsyncFakeRedis, async_runner
) -> None:
    cfg = CacheConfig(timeout_seconds=10)
    cfg.disk_path = str(tmp_path)
    cache = IntelligentMultiLevelCache(cfg)
    cache.memory_limit = 1

    async_runner(cache.start())
    async_runner(cache.set("a", 1))

    cache._memory.clear()
    async_runner(fake_redis.flushdb())

    value = async_runner(cache.get("a"))
    assert value == 1
    assert "a" in cache._memory
    assert async_runner(fake_redis.get(cache._full_key("a"))) is not None

    async_runner(cache.set("b", 2))
    assert "a" not in cache._memory and "b" in cache._memory
    assert (tmp_path / f"{cache._full_key('a')}.json").exists()
    async_runner(cache.stop())


def test_ttl_expiration(
    tmp_path: Path, fake_redis: AsyncFakeRedis, async_runner
) -> None:
    cfg = CacheConfig(timeout_seconds=1)
    cfg.disk_path = str(tmp_path)
    cache = IntelligentMultiLevelCache(cfg)

    async_runner(cache.start())
    async_runner(cache.set("k", "v", ttl=1))
    async_runner(asyncio.sleep(1.1))

    assert async_runner(cache.get("k")) is None
    assert "k" not in cache._memory
    assert async_runner(fake_redis.get(cache._full_key("k"))) is None
    assert not (tmp_path / f"{cache._full_key('k')}.json").exists()
    async_runner(cache.stop())


def test_cache_with_lock_sync_and_async(async_runner) -> None:
    cfg = CacheConfig(timeout_seconds=5)
    manager = InMemoryCacheManager(cfg)
    async_runner(manager.start())

    calls_async = {"count": 0}

    @cache_with_lock(manager, ttl=10)
    async def afunc(x: int) -> int:
        calls_async["count"] += 1
        await asyncio.sleep(0)
        return x * 2

    assert async_runner(afunc(2)) == 4
    assert async_runner(afunc(2)) == 4
    assert calls_async["count"] == 1
    async_runner(manager.clear())
    assert async_runner(afunc(2)) == 4
    assert calls_async["count"] == 2

    calls_sync = {"count": 0}

    @cache_with_lock(manager, ttl=10)
    def sfunc(x: int) -> int:
        calls_sync["count"] += 1
        return x + 1

    assert sfunc(3) == 4
    assert sfunc(3) == 4
    assert calls_sync["count"] == 1
    async_runner(manager.clear())
    assert sfunc(3) == 4
    assert calls_sync["count"] == 2

    async_runner(manager.stop())


def _loader(key: str) -> str:
    return f"value-{key}"


def test_cache_warming(async_runner) -> None:
    cache = HierarchicalCacheManager()
    warmer = IntelligentCacheWarmer(cache, _loader)

    warmer.record_usage("alpha")
    warmer.record_usage("beta")
    warmer.record_usage("alpha")

    async_runner(warmer.warm())

    assert cache.get("alpha") == "value-alpha"
    assert cache.get("beta") == "value-beta"
    assert "alpha" in cache._level1 and "alpha" in cache._level2

