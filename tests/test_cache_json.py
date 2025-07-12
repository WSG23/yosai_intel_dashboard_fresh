import advanced_cache

def test_json_serialization_roundtrip(tmp_path, monkeypatch):
    class Dummy:
        def __init__(self, x):
            self.x = x
    # use in-memory cache by monkeypatching get_redis_client to None
    monkeypatch.setattr(advanced_cache, "get_redis_client", lambda: None)
    obj = {"a": 1}
    advanced_cache.set_cache_value("k", obj)
    assert advanced_cache.get_cache_value("k") == obj
