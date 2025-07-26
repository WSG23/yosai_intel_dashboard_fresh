from services.analytics.storage.cache import cached, _cache_manager


@cached(ttl=1)
def plus_one(x):
    return x + 1


def test_cached_decorator(monkeypatch):
    assert plus_one(1) == 2
    assert plus_one(1) == 2  # cached
