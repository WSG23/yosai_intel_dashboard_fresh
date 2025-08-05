from __future__ import annotations

from flask import Flask

from yosai_intel_dashboard.src.core import cache as cache_module


def test_init_app_configures_cache(monkeypatch):
    app = Flask(__name__)
    called = {}

    def fake_init(app_, config=None, **kwargs):
        called["config"] = config
        app_.extensions["cache"] = cache_module.cache

    monkeypatch.setattr(cache_module.cache, "init_app", fake_init)

    cache_module.init_app(app)

    assert called["config"]["CACHE_TYPE"] == "simple"
    assert app.extensions["cache"] is cache_module.cache


def test_init_app_fallback(monkeypatch):
    app = Flask(__name__)
    original_cache = cache_module.cache

    def failing_init(self, app_, config):
        raise RuntimeError("boom")

    monkeypatch.setattr(cache_module.cache, "init_app", failing_init)

    cache_module.init_app(app)
    cache_module.cache.set("foo", "bar")

    assert cache_module.cache.get("foo") == "bar"
    assert "cache" in app.extensions

    cache_module.cache = original_cache
