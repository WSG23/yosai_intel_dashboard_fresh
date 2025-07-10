import importlib
import types


def test_redis_cache_manager_fallback(monkeypatch, fake_dash):
    cm = importlib.import_module("core.plugins.config.cache_manager")

    class FakeRedis:
        def __init__(self, *args, **kwargs):
            pass

        def ping(self):
            raise ConnectionError("unreachable")

    monkeypatch.setattr(cm, "redis", types.SimpleNamespace(Redis=FakeRedis))
    cfg = types.SimpleNamespace(host="localhost", port=6379, db=0, ttl=1)
    manager = cm.RedisCacheManager(cfg)

    manager.start()  # should fall back to memory cache
    manager.set("foo", "bar")
    assert manager.get("foo") == "bar"
    manager.stop()
