import sys
from dash import Dash, html

from core.plugins.auto_config import setup_plugins
from core.container import Container as DIContainer
from config.config import ConfigManager

from tests.test_auto_configuration import _set_env, _create_package


def test_plugin_discovery_and_callback_registration(monkeypatch, tmp_path):
    _set_env(monkeypatch)
    _create_package(tmp_path)
    sys.path.insert(0, str(tmp_path))
    registry = None
    try:
        app = Dash(__name__)
        app.layout = html.Div()
        registry = setup_plugins(
            app,
            container=DIContainer(),
            config_manager=ConfigManager(),
            package="auto_pkg",
        )
        assert "auto_plugin" in registry.plugin_manager.plugins
        assert "auto_cb" in registry.coordinator.registered_callbacks
        routes = [r.rule for r in app.server.url_map.iter_rules()]
        assert "/health/plugins" in routes
    finally:
        sys.path.remove(str(tmp_path))
        if registry:
            registry.plugin_manager.stop_health_monitor()
