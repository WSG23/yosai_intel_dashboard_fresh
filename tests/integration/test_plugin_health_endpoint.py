import sys
import types
import importlib.util
import enum
from flask.json.provider import DefaultJSONProvider

# Minimal services stubs
spec = importlib.util.spec_from_file_location("services.data_processing.core.protocols", "tests/stubs/protocols_stub.py")
protocols_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocols_mod)

services_mod = types.ModuleType("services")
registry_mod = types.ModuleType("services.registry")
registry_mod.get_service = lambda name: None
services_mod.registry = registry_mod

core_mod = types.ModuleType("services.data_processing.core")
core_mod.protocols = protocols_mod

data_proc_mod = types.ModuleType("services.data_processing")
data_proc_mod.core = core_mod
services_mod.data_processing = data_proc_mod

sys.modules["services"] = services_mod
sys.modules["services.registry"] = registry_mod
sys.modules["services.data_processing"] = data_proc_mod
sys.modules["services.data_processing.core"] = core_mod
sys.modules["services.data_processing.core.protocols"] = protocols_mod

import pytest
from flask import Flask
from core.service_container import ServiceContainer
from core.plugins.manager import PluginManager
from config import create_config_manager
from services.data_processing.core.protocols import PluginMetadata

class EnumJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, enum.Enum):
            return o.name
        return super().default(o)

class DummyPlugin:
    metadata = PluginMetadata(name="dummy", version="0.1", description="d", author="t")

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

    def register_callbacks(self, manager, container):
        return True


@pytest.mark.integration
def test_health_endpoint_returns_status():
    app = Flask(__name__)
    app.json_provider_class = EnumJSONProvider
    app.json = app.json_provider_class(app)
    cfg = create_config_manager()
    manager = PluginManager(ServiceContainer(), cfg, health_check_interval=1)
    manager.load_plugin(DummyPlugin())
    manager.register_health_endpoint(app)

    client = app.test_client()
    resp = client.get("/health/plugins")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "dummy" in data
    assert data["dummy"]["health"]["healthy"] is True
    manager.stop_health_monitor()
