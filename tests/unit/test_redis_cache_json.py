import importlib
import json
import pickle
import sys
import types
from yosai_intel_dashboard.src.core.imports.resolver import safe_import



def _setup_manager(monkeypatch, fake_redis):
    sys.modules.setdefault(
        "config.database_manager",
        types.SimpleNamespace(DatabaseManager=object, MockConnection=object),
    )
    redis_mod = sys.modules["redis"]
    redis_mod.Redis = lambda *a, **k: fake_redis
    cm = importlib.import_module("core.plugins.config.cache_manager")
    monkeypatch.setattr(
        cm, "redis", types.SimpleNamespace(Redis=lambda *a, **k: fake_redis)
    )
    cfg = types.SimpleNamespace(host="localhost", port=6379, db=0, ttl=1)
    manager = cm.RedisCacheManager(cfg)
    manager.start()
    return manager


class FakeRedis:
    def __init__(self):
        self.store = {}

    def ping(self):
        return True

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value

    def setex(self, key, ttl, value):
        self.set(key, value)

    def delete(self, key):
        return bool(self.store.pop(key, None))

    def flushdb(self):
        self.store.clear()


def test_redis_cache_json_roundtrip(monkeypatch):
    fake = FakeRedis()
    manager = _setup_manager(monkeypatch, fake)
    value = {"a": 1}
    manager.set("foo", value)
    assert fake.store["foo"] == json.dumps(value).encode("utf-8")
    assert manager.get("foo") == value
    manager.stop()


def test_redis_cache_migrates_pickle(monkeypatch):
    fake = FakeRedis()
    orig = {"legacy": True}
    fake.store["foo"] = pickle.dumps(orig)
    manager = _setup_manager(monkeypatch, fake)
    assert manager.get("foo") == orig
    assert fake.store["foo"] == json.dumps(orig).encode("utf-8")
    manager.stop()
