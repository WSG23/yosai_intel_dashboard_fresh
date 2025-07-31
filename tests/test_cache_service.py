from yosai_intel_dashboard.src.services.analytics.storage.cache import _cache_manager, cached


@cached(ttl=1)
def plus_one(x):
    return x + 1


def test_cached_decorator(monkeypatch):
    assert plus_one(1) == 2
    assert plus_one(1) == 2  # cached
