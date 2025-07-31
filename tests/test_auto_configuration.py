from __future__ import annotations

import os
import sys

import pytest
from dash import Dash, Input, Output

from config import create_config_manager
from core.json_serialization_plugin import JsonSerializationPlugin
from core.plugins.auto_config import setup_plugins
from core.plugins.callback_unifier import CallbackUnifier
from core.plugins.decorators import safe_callback
from core.protocols.plugin import PluginMetadata
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer

pytestmark = pytest.mark.usefixtures("fake_dash")

REQUIRED_VARS = [
    "SECRET_KEY",
    "DB_PASSWORD",
    "AUTH0_CLIENT_ID",
    "AUTH0_CLIENT_SECRET",
    "AUTH0_DOMAIN",
    "AUTH0_AUDIENCE",
]


def _set_env(monkeypatch):
    for var in REQUIRED_VARS:
        monkeypatch.setenv(var, "test")


def _create_package(tmp_path):
    pkg = tmp_path / "auto_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    plugin_code = """
from dash import Output, Input
from core.protocols.plugin import PluginMetadata
from core.plugins.callback_unifier import CallbackUnifier

class AutoPlugin:
    metadata = PluginMetadata(
        name="auto_plugin",
        version="0.1",
        description="auto plugin",
        author="tester",
    )

    def __init__(self):
        self.callback_registered = False

    def load(self, container, config):
        container.register("auto_service", "ok")
        return True

    def configure(self, config):
        return True

    def start(self):
        return True

    def stop(self):
        return True

    def health_check(self):
        return {"healthy": True}

    def register_callbacks(self, manager, container):
        @CallbackUnifier(manager)(
            Output("out", "children"),
            Input("in", "value"),
            callback_id="auto_cb",
            component_name="AutoPlugin",
        )
        def cb(value):
            return f"auto:{value}"

        self.callback_registered = True
        return True

def create_plugin():
    return AutoPlugin()
"""
    (pkg / "plug.py").write_text(plugin_code)
    return pkg


def test_setup_uses_provided_dependencies(monkeypatch, tmp_path):
    _set_env(monkeypatch)
    pkg = _create_package(tmp_path)
    sys.path.insert(0, str(tmp_path))
    registry = None
    try:
        app = Dash(__name__)
        container = ServiceContainer()
        config = create_config_manager()
        config.config.plugin_settings["auto_plugin"] = {"enabled": True}
        registry = setup_plugins(
            app, container=container, config_manager=config, package="auto_pkg"
        )
        assert registry.container is container
        assert registry.plugin_manager.container is container
        assert registry.plugin_manager.config_manager is config
    finally:
        sys.path.remove(str(tmp_path))
        if registry:
            registry.plugin_manager.stop_health_monitor()


def test_setup_loads_and_registers_callbacks(monkeypatch, tmp_path):
    _set_env(monkeypatch)
    pkg = _create_package(tmp_path)
    sys.path.insert(0, str(tmp_path))
    registry = None
    try:
        app = Dash(__name__)
        registry = setup_plugins(app, package="auto_pkg")
        assert "auto_plugin" in registry.plugin_manager.plugins
        plugin = registry.plugin_manager.plugins["auto_plugin"]
        assert registry.container.has("auto_service")
        assert plugin.callback_registered
        assert "auto_cb" in registry.coordinator.registered_callbacks
        routes = [r.rule for r in app.server.url_map.iter_rules()]
        assert "/health/plugins" in routes
    finally:
        sys.path.remove(str(tmp_path))
        if registry:
            registry.plugin_manager.stop_health_monitor()


def test_setup_exposes_container_and_safe_callback(monkeypatch):
    """Ensure setup_plugins attaches container and safe_callback uses it."""
    _set_env(monkeypatch)
    app = Dash(__name__)

    registry = setup_plugins(app)
    try:
        assert hasattr(app, "_yosai_container")

        container = app._yosai_container

        plugin = JsonSerializationPlugin()
        plugin.load(container, {"enabled": True})

        @safe_callback(app)
        def cb():
            import pandas as pd

            return pd.DataFrame({"A": [1, 2]})

        result = cb()
        assert isinstance(result, dict)
        assert result.get("__type__") == "DataFrame"
    finally:
        registry.plugin_manager.stop_health_monitor()
