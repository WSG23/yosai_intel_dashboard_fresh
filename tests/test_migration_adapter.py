import importlib.util
import os
import pathlib
import sys
import types
from typing import Any

import pandas as pd

# Provide a lightweight stub for services.interfaces to avoid heavy imports
stub_pkg = types.ModuleType("services")
stub_interfaces = types.ModuleType("services.interfaces")


class AnalyticsServiceProtocol:
    pass


stub_interfaces.AnalyticsServiceProtocol = AnalyticsServiceProtocol
sys.modules.setdefault("services", stub_pkg)
sys.modules["services.interfaces"] = stub_interfaces

spec = importlib.util.spec_from_file_location(
    "migration_adapter",
    pathlib.Path(__file__).resolve().parents[1]
    / "services"
    / "migration"
    / "adapter.py",
)
migration_adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_adapter)

ServiceAdapter = migration_adapter.ServiceAdapter
EventServiceAdapter = migration_adapter.EventServiceAdapter
AnalyticsServiceAdapter = migration_adapter.AnalyticsServiceAdapter
MigrationContainer = migration_adapter.MigrationContainer
register_migration_services = migration_adapter.register_migration_services


class DummyAnalytics:
    def __init__(self):
        self.called = False

    def get_dashboard_summary(self) -> dict:
        self.called = True
        return {"status": "ok"}

    def get_access_patterns_analysis(self, days: int = 7) -> dict:
        return {"days": days}

    def process_dataframe(self, df: pd.DataFrame) -> dict:
        return {"rows": len(df)}


class DummyAdapter(ServiceAdapter):
    async def call(self, method: str, **kwargs: Any) -> Any:
        return {"method": method, **kwargs}


def test_migration_container_registration():
    container = MigrationContainer()
    adapter = DummyAdapter()
    container.register_with_adapter("demo", None, adapter)
    assert container.get("demo") is adapter
    status = container.get_migration_status()
    assert status["services"]["demo"]["adapter_type"] == "DummyAdapter"
    assert status["services"]["demo"]["using_microservice"] is True


def test_analytics_service_adapter_fallback(monkeypatch):
    os.environ["USE_ANALYTICS_MICROSERVICE"] = "true"
    dummy = DummyAnalytics()
    adapter = AnalyticsServiceAdapter(dummy)

    async def fail_call(method: str, params: dict):
        raise RuntimeError("boom")

    monkeypatch.setattr(adapter, "_call_microservice", fail_call)
    result = adapter.get_dashboard_summary()
    assert result == {"status": "ok"}
    assert dummy.called is True
