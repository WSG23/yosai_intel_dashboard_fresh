import os
import time

from yosai_intel_dashboard.src.core.cache_manager import CacheConfig, InMemoryCacheManager, cache_with_lock

manager = InMemoryCacheManager(CacheConfig())


def test_per_endpoint_ttl(monkeypatch):
    monkeypatch.setenv("CACHE_TTL_MYFUNC", "1")

    calls = {"count": 0}

    @cache_with_lock(manager, ttl=10, name="myfunc")
    def myfunc(x):
        calls["count"] += 1
        return x * 2

    assert myfunc(2) == 4
    assert myfunc(2) == 4
    assert calls["count"] == 1

    time.sleep(1.1)
    assert myfunc(2) == 4
    assert calls["count"] == 2
