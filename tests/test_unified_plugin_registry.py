from dash import Dash
import sys
import os
from core.plugins.unified_registry import UnifiedPluginRegistry
from core.plugins.auto_config import PluginAutoConfiguration
from core.plugins.protocols import PluginMetadata
from core.container import Container as DIContainer
from config.config import ConfigManager


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
    os.environ.setdefault("SECRET_KEY", "test")
    os.environ.setdefault("DB_PASSWORD", "pwd")
    os.environ.setdefault("AUTH0_CLIENT_ID", "cid")
    os.environ.setdefault("AUTH0_CLIENT_SECRET", "csecret")
    os.environ.setdefault("AUTH0_DOMAIN", "domain")
    os.environ.setdefault("AUTH0_AUDIENCE", "aud")
    app = Dash(__name__)
    container = DIContainer()
    registry = UnifiedPluginRegistry(app, container, ConfigManager())
    plugin = DummyPlugin()
    assert registry.register_plugin(plugin)
    registry.auto_configure_callbacks()
    assert plugin.registered
    assert registry.get_plugin_service("dummy_service") == "value"


def test_auto_discovery_and_health_endpoint(tmp_path):
    os.environ.setdefault("SECRET_KEY", "test")
    os.environ.setdefault("DB_PASSWORD", "pwd")
    os.environ.setdefault("AUTH0_CLIENT_ID", "cid")
    os.environ.setdefault("AUTH0_CLIENT_SECRET", "csecret")
    os.environ.setdefault("AUTH0_DOMAIN", "domain")
    os.environ.setdefault("AUTH0_AUDIENCE", "aud")
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
        plugin_auto = PluginAutoConfiguration(app, package="auto_pkg")
        plugin_auto.scan_and_configure("auto_pkg")
        plugin_auto.generate_health_endpoints()
        registry = plugin_auto.registry
        assert "dummy" in registry.plugin_manager.plugins
        rules = [r.rule for r in app.server.url_map.iter_rules()]
        assert "/health/plugins" in rules
    finally:
        sys.path.remove(str(tmp_path))
        if registry:
            registry.plugin_manager.stop_health_monitor()


def test_validate_plugin_dependencies():
    """Ensure dependency validation reports missing dependencies."""
    os.environ.setdefault("SECRET_KEY", "test")
    os.environ.setdefault("DB_PASSWORD", "pwd")
    os.environ.setdefault("AUTH0_CLIENT_ID", "cid")
    os.environ.setdefault("AUTH0_CLIENT_SECRET", "csecret")
    os.environ.setdefault("AUTH0_DOMAIN", "domain")
    os.environ.setdefault("AUTH0_AUDIENCE", "aud")
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
