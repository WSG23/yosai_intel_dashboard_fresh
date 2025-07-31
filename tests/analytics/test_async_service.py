import asyncio
from types import SimpleNamespace

import pytest

from yosai_intel_dashboard.src.services.analytics.async_service import AsyncAnalyticsService


class _DummyContext:
    async def __aenter__(self):
        return SimpleNamespace()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummyPool:
    def __init__(self):
        self.acquire_calls = 0

    async def acquire(self):
        self.acquire_calls += 1
        return _DummyContext()


class DummyRepo:
    def __init__(self):
        self.pool = DummyPool()
        self.summary_calls = 0
        self.pattern_calls = 0

    async def fetch_dashboard_summary(self, conn, days=7):
        self.summary_calls += 1
        return {"days": days}

    async def fetch_access_patterns(self, conn, days=7):
        self.pattern_calls += 1
        return {"patterns": days}


class DummyLock:
    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummyCache:
    def __init__(self):
        self.data = {}
        self.started = False
        self.stopped = False

    async def start(self):
        self.started = True

    async def stop(self):
        self.stopped = True

    def get_lock(self, key):
        return DummyLock()

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ttl):
        self.data[key] = value


@pytest.mark.asyncio
async def test_dashboard_summary_caching():
    repo = DummyRepo()
    cache = DummyCache()
    service = AsyncAnalyticsService(repo, cache_manager=cache)
    await service.start()
    res1 = await service.get_dashboard_summary(5)
    res2 = await service.get_dashboard_summary(5)
    await service.stop()
    assert res1 == {"days": 5}
    assert res2 == {"days": 5}
    assert repo.summary_calls == 1
    assert cache.started and cache.stopped


@pytest.mark.asyncio
async def test_combined_analytics_error():
    repo = DummyRepo()

    async def bad_fetch(*a, **k):
        raise RuntimeError("boom")

    repo.fetch_dashboard_summary = bad_fetch
    service = AsyncAnalyticsService(repo, cache_manager=DummyCache())
    result = await service.get_combined_analytics()
    assert result["status"] == "error"
