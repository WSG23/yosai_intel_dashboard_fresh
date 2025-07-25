import os

from yosai_intel_dashboard.src.core import app_factory
from yosai_intel_dashboard.src.infrastructure.config import reload_config


def test_csrf_plugin_enabled_in_production(monkeypatch):
    monkeypatch.setenv("YOSAI_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "testkey")
    monkeypatch.setenv("DB_PASSWORD", "dummy")
    monkeypatch.setenv("AUTH0_CLIENT_ID", "dummy")
    monkeypatch.setenv("AUTH0_CLIENT_SECRET", "dummy")
    monkeypatch.setenv("AUTH0_DOMAIN", "dummy")
    monkeypatch.setenv("AUTH0_AUDIENCE", "dummy")
    reload_config()

    from yosai_intel_dashboard.src.core.plugins import PluginManager

    monkeypatch.setattr(PluginManager, "load_all_plugins", lambda self: None)

    def _fake_csrf(app, mode=None):
        app.server.config["WTF_CSRF_ENABLED"] = True
        app._csrf_plugin = object()
        return app._csrf_plugin

    monkeypatch.setattr(
        "core.app_factory.security.setup_enhanced_csrf_protection", _fake_csrf
    )
    monkeypatch.setattr(app_factory, "_initialize_services", lambda *a, **k: None)
    monkeypatch.setattr(app_factory, "_register_global_callbacks", lambda manager: None)

    app = app_factory.create_app(mode="full")
    server = app.server
    assert server.config["WTF_CSRF_ENABLED"] is True
    assert hasattr(app, "_csrf_plugin")
