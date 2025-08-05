from __future__ import annotations

import enum

import pytest
from dash import Dash, html
from flask.json.provider import DefaultJSONProvider


class EnumJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, enum.Enum):
            return o.name
        return super().default(o)


import sys

from yosai_intel_dashboard.src.core.plugins.auto_config import PluginAutoConfiguration
from yosai_intel_dashboard.src.core.plugins.unified_registry import (
    UnifiedPluginRegistry,
)
from yosai_intel_dashboard.src.infrastructure.config import create_config_manager
from yosai_intel_dashboard.src.infrastructure.di.service_container import (
    ServiceContainer,
)

pytestmark = pytest.mark.usefixtures("fake_dash")
from yosai_intel_dashboard.src.core.protocols.plugin import PluginMetadata


class DummyPlugin:
    metadata = PluginMetadata(
        name="dummy",
        version="0.1",
        description="test",
        author="tester",
    )

    def __init__(self):
        self.registered = False

    def load(self, container, config):
        container.register("dummy_service", "value")
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
        self.registered = True
        return True


def test_registry_registration_and_service():
    app = Dash(__name__)
    container = ServiceContainer()
    cfg = create_config_manager()
    cfg.config.plugin_settings["dummy"] = {"enabled": True}
    registry = UnifiedPluginRegistry(app, container, cfg)
    plugin = DummyPlugin()
    assert registry.register_plugin(plugin)
    registry.auto_configure_callbacks()
    assert plugin.registered
    assert registry.get_plugin_service("dummy_service") == "value"


def test_auto_discovery_and_health_endpoint(tmp_path):
    pkg = tmp_path / "auto_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "plug.py").write_text(
        """
from tests.test_unified_plugin_registry import DummyPlugin

def create_plugin():
    return DummyPlugin()
"""
    )
    sys.path.insert(0, str(tmp_path))
    registry = None
    try:
        app = Dash(__name__)
        app.layout = html.Div()
        app.server.json_provider_class = EnumJSONProvider
        app.server.json = app.server.json_provider_class(app.server)
        plugin_auto = PluginAutoConfiguration(app, package="auto_pkg")
        plugin_auto.scan_and_configure("auto_pkg")
        plugin_auto.generate_health_endpoints()
        registry = plugin_auto.registry
        assert "dummy" in registry.plugin_manager.plugins
        rules = [r.rule for r in app.server.url_map.iter_rules()]
        assert "/health/plugins" in rules
        client = app.server.test_client()
        resp = client.get("/health/plugins")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["dummy"]["health"]["healthy"] is True
    finally:
        sys.path.remove(str(tmp_path))
        if registry:
            registry.plugin_manager.stop_health_monitor()


def test_validate_plugin_dependencies():
    """Ensure dependency validation reports missing dependencies."""
    app = Dash(__name__)
    auto = PluginAutoConfiguration(app)

    class DepPlugin(DummyPlugin):
        metadata = PluginMetadata(
            name="dep",
            version="0.1",
            description="dep",
            author="tester",
            dependencies=["missing"],
        )

    plugin = DepPlugin()
    auto.registry.register_plugin(plugin)
    missing = auto.validate_plugin_dependencies()
    assert "dep:missing" in missing
