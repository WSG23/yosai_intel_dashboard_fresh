from flask import Flask
import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parent.parent))

# Stub config.config to avoid heavy dependencies
config_stub = types.ModuleType("config.config")

class DummyConfigManager:
    def __init__(self, *args, **kwargs) -> None:
        pass

config_stub.ConfigManager = DummyConfigManager
sys.modules.setdefault("config.config", config_stub)

from core.unified_plugin_registry import UnifiedPluginRegistry
from core.plugins.protocols import PluginMetadata


class DummyPlugin:
    metadata = PluginMetadata(
        name="dummy",
        version="0.1",
        description="d",
        author="tester",
    )

    def load(self, container, config):
        return True

    def configure(self, config):
        return True

    def start(self):
        return True

    def stop(self):
        return True

    def health_check(self):
        return {"healthy": True}


import unittest


class TestUnifiedPluginRegistry(unittest.TestCase):
    def test_register_plugin_adds_health_route(self):
        server = Flask(__name__)
        registry = UnifiedPluginRegistry(server)
        plugin = DummyPlugin()

        self.assertTrue(registry.register_plugin(plugin))

        routes = {rule.rule for rule in server.url_map.iter_rules()}
        self.assertIn("/health/plugins", routes)

        health = registry.get_health()
        self.assertIn("dummy", health)

        registry.shutdown()


if __name__ == "__main__":
    unittest.main()
