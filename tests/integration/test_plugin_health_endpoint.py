from __future__ import annotations

import enum
import importlib.util
import sys
import types

from flask.json.provider import DefaultJSONProvider

from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# Minimal services stubs
spec = importlib.util.spec_from_file_location(
    "core.protocols.plugin", "tests/unit/stubs/protocols_stub.py"
)
protocols_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocols_mod)

services_mod = types.ModuleType("services")
registry_mod = types.ModuleType("core.registry")
registry_mod.get_service = lambda name: None

core_mod = types.ModuleType("services.data_processing.core")
core_mod.protocols = protocols_mod

data_proc_mod = types.ModuleType("services.data_processing")
data_proc_mod.core = core_mod
services_mod.data_processing = data_proc_mod

safe_import("services", services_mod)
safe_import("core.registry", registry_mod)
safe_import("services.data_processing", data_proc_mod)
safe_import("services.data_processing.core", core_mod)
safe_import("core.protocols.plugin", protocols_mod)

import pytest
from flask import Flask

from yosai_intel_dashboard.src.core.plugins.manager import PluginManager
from yosai_intel_dashboard.src.core.protocols.plugin import PluginMetadata
from yosai_intel_dashboard.src.infrastructure.config import create_config_manager
from yosai_intel_dashboard.src.infrastructure.di.service_container import (
    ServiceContainer,
)


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
