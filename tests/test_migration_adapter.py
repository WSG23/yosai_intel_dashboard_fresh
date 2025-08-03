import importlib.util
import os
import pathlib
import sys
import types
from typing import Any

import pandas as pd
from tests.import_helpers import safe_import, import_optional

# Provide a lightweight stub for services.interfaces to avoid heavy imports
stub_pkg = types.ModuleType("services")
stub_interfaces = types.ModuleType("services.interfaces")

# Load the feature flag module so adapter imports succeed
flags_spec = importlib.util.spec_from_file_location(
    "services.feature_flags",
    pathlib.Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "services"
    / "feature_flags"
    / "__init__.py",
)
flags_module = importlib.util.module_from_spec(flags_spec)
flags_spec.loader.exec_module(flags_module)
stub_pkg.feature_flags = flags_module
safe_import('services.feature_flags', flags_module)

# Minimal registry stub
registry_stub = types.ModuleType("services.registry")


class ServiceDiscovery:
    def resolve(self, name: str) -> str | None:
        return None


registry_stub.ServiceDiscovery = ServiceDiscovery
stub_pkg.registry = registry_stub
safe_import('services.registry', registry_stub)

# Minimal resilience.circuit_breaker stub
resilience_pkg = types.ModuleType("services.resilience")
cb_module = types.ModuleType("services.resilience.circuit_breaker")


class CircuitBreaker:
    def __init__(self, *args, **kwargs):
        pass


class CircuitBreakerOpen(Exception):
    pass


cb_module.CircuitBreaker = CircuitBreaker
cb_module.CircuitBreakerOpen = CircuitBreakerOpen
resilience_pkg.circuit_breaker = cb_module
stub_pkg.resilience = resilience_pkg
safe_import('services.resilience', resilience_pkg)
safe_import('services.resilience.circuit_breaker', cb_module)


class AnalyticsServiceProtocol:
    pass


stub_interfaces.AnalyticsServiceProtocol = AnalyticsServiceProtocol
safe_import('services', stub_pkg)
safe_import('services.interfaces', stub_interfaces)

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
    monkeypatch.setitem(
        migration_adapter.feature_flags._flags, "use_analytics_microservice", False
    )
    dummy = DummyAnalytics()
    adapter = AnalyticsServiceAdapter(dummy)

    async def fail_call(method: str, params: dict):
        raise RuntimeError("boom")

    monkeypatch.setattr(adapter, "_call_microservice", fail_call)
    result = adapter.get_dashboard_summary()
    assert result == {"status": "ok"}
    assert dummy.called is True
