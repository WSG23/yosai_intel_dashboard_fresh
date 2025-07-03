import os
from core import app_factory
from config.config import reload_config


def test_csrf_plugin_enabled_in_production(monkeypatch):
    monkeypatch.setenv("YOSAI_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "testkey")
    monkeypatch.setenv("DB_PASSWORD", "dummy")
    reload_config()

    monkeypatch.setattr(
        app_factory.PluginManager, "load_all_plugins", lambda self: None
    )
    monkeypatch.setattr(app_factory, "_initialize_services", lambda: None)
    monkeypatch.setattr(app_factory, "_register_router_callbacks", lambda manager: None)
    monkeypatch.setattr(app_factory, "_register_global_callbacks", lambda manager: None)

    app = app_factory.create_app(mode="full")
    server = app.server
    assert server.config["WTF_CSRF_ENABLED"] is True
    assert hasattr(app, "_csrf_plugin")
