import sys

from dash import Dash, html

from config.config import ConfigManager
from core.container import Container as DIContainer
from core.plugins.auto_config import setup_plugins
from tests.test_auto_configuration import _set_env
from tests.utils.plugin_package_builder import PluginPackageBuilder


def test_plugin_discovery_and_callback_registration(monkeypatch, tmp_path):
    _set_env(monkeypatch)
    registry = None
    with PluginPackageBuilder(tmp_path) as builder:
        try:
            app = Dash(__name__)
            app.layout = html.Div()
            cfg = ConfigManager()
            cfg.config.plugin_settings[builder.plugin_name] = {"enabled": True}
            registry = setup_plugins(
                app,
                container=DIContainer(),
                config_manager=cfg,
                package=builder.package_name,
            )
            assert builder.plugin_name in registry.plugin_manager.plugins
            assert builder.callback_id in registry.coordinator.registered_callbacks
            routes = [r.rule for r in app.server.url_map.iter_rules()]
            assert "/health/plugins" in routes
        finally:
            if registry:
                registry.plugin_manager.stop_health_monitor()
