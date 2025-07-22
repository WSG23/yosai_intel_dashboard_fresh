import os
import time

import advanced_cache

class SimpleCache:
    def __init__(self):
        self.store = {}
    def get(self, key):
        val, exp = self.store.get(key, (None, None))
        if exp is not None and time.time() > exp:
            self.store.pop(key, None)
            return None
        return val
    def set(self, key, value, timeout=None, ttl=None):
        expiry = time.time() + float(timeout or ttl or 0) if (timeout or ttl) else None
        self.store[key] = (value, expiry)
    def delete(self, key):
        self.store.pop(key, None)
    def clear(self):
        self.store.clear()


def test_per_endpoint_ttl(monkeypatch):
    monkeypatch.setattr(advanced_cache, "get_redis_client", lambda: None)
    monkeypatch.setattr(advanced_cache, "cache", SimpleCache())
    monkeypatch.setenv("CACHE_TTL_MYFUNC", "1")

    calls = {"count": 0}

    @advanced_cache.cache_with_lock(ttl_seconds=10, name="myfunc")
    def myfunc(x):
        calls["count"] += 1
        return x * 2

    assert myfunc(2) == 4
    assert myfunc(2) == 4
    assert calls["count"] == 1

    time.sleep(1.1)
    assert myfunc(2) == 4
    assert calls["count"] == 2
