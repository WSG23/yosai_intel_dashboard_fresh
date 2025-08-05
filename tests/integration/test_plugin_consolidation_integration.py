import sys

import pytest
from dash import Dash, html

from tests.test_auto_configuration import _set_env
from tests.utils.plugin_package_builder import PluginPackageBuilder
from yosai_intel_dashboard.src.core.plugins.auto_config import setup_plugins
from yosai_intel_dashboard.src.infrastructure.config import create_config_manager
from yosai_intel_dashboard.src.infrastructure.di.service_container import (
    ServiceContainer,
)

pytestmark = pytest.mark.usefixtures("fake_dash")


def test_plugin_discovery_and_callback_registration(monkeypatch, tmp_path):
    _set_env(monkeypatch)
    registry = None
    with PluginPackageBuilder(tmp_path) as builder:
        try:
            app = Dash(__name__)
            app.layout = html.Div()
            cfg = create_config_manager()
            cfg.config.plugin_settings[builder.plugin_name] = {"enabled": True}
            registry = setup_plugins(
                app,
                container=ServiceContainer(),
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
