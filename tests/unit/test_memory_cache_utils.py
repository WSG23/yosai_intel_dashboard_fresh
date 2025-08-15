import importlib
import threading
import time


def test_memory_cache_ttl(fake_dash):
    cache_mod = importlib.import_module("core.caching")
    cache = cache_mod.MemoryCache(default_ttl=1)
    cache.set("foo", "bar")
    assert cache.get("foo") == "bar"
    time.sleep(1.1)
    assert cache.get("foo") is None


def test_cached_concurrent_calls(fake_dash):
    cache_mod = importlib.import_module("core.caching")

    counter = {"calls": 0}
    count_lock = threading.Lock()

    @cache_mod.cached(ttl=10)
    def compute(value):
        with count_lock:
            counter["calls"] += 1
        time.sleep(0.05)
        return value * 2

    results = []
    threads = [
        threading.Thread(target=lambda: results.append(compute(5))) for _ in range(5)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results == [10] * 5
    assert counter["calls"] == 1
