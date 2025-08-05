from __future__ import annotations

import types

from yosai_intel_dashboard.src.core import cache as cache_module


class DummyCache:
    def __init__(self) -> None:
        self.called = None

    def init_app(self, app, config):
        self.called = (app, config)


def test_init_app_calls_cache(monkeypatch):
    app = types.SimpleNamespace(extensions={})
    dummy = DummyCache()
    monkeypatch.setattr(cache_module, "cache", dummy)
    cache_module.init_app(app)
    assert dummy.called is not None
    assert dummy.called[1]["CACHE_TYPE"] == "simple"


def test_init_app_fallback(monkeypatch):
    app = types.SimpleNamespace(extensions={})

    class FailCache:
        def init_app(self, app, config):
            raise Exception("fail")

    original_cache = cache_module.cache
    monkeypatch.setattr(cache_module, "cache", FailCache())
    cache_module.init_app(app)
    cache_module.cache.set("foo", "bar")
    assert cache_module.cache.get("foo") == "bar"
    cache_module.cache.delete("foo")
    assert cache_module.cache.get("foo") is None
    cache_module.cache.set("foo", "bar")
    cache_module.cache.clear()
    assert cache_module.cache.get("foo") is None
    assert app.extensions["cache"] is cache_module.cache
    cache_module.cache = original_cache
