import importlib.util
import os
import pathlib

import pytest
from fastapi.testclient import TestClient
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# Use lightweight imports
os.environ["LIGHTWEIGHT_SERVICES"] = "1"
os.environ.setdefault("JWT_SECRET_KEY", os.urandom(16).hex())

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"

# Load the FastAPI analytics microservice
app_spec = importlib.util.spec_from_file_location(
    "services.analytics_microservice.app",
    SERVICES_PATH / "analytics_microservice" / "app.py",
)
app_module = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(app_module)

from yosai_intel_dashboard.src.services.migration import adapter as migration_adapter


class DummyAnalytics:
    def get_dashboard_summary(self) -> dict:
        return {"status": "ok"}

    def get_access_patterns_analysis(self, days: int = 7) -> dict:
        return {"days": days}


# Patch create_analytics_service to return our dummy instance
import types

analytics_stub = types.ModuleType("services.analytics_service")
analytics_stub.create_analytics_service = lambda: DummyAnalytics()
import sys

safe_import('services.analytics_service', analytics_stub)


@pytest.mark.integration
def test_analytics_service_adapter_microservice(monkeypatch):
    """Adapter should return the same data as the microservice."""
    monkeypatch.setenv("USE_GO_ANALYTICS", "true")
    monkeypatch.setitem(
        migration_adapter.feature_flags._flags, "use_analytics_microservice", True
    )

    client = TestClient(app_module.app)

    async def _local_call(self, method: str, params: dict):
        resp = client.post(f"/v1/analytics/{method}", json=params)
        return resp.json()

    monkeypatch.setattr(
        migration_adapter.AnalyticsServiceAdapter,
        "_call_microservice",
        _local_call,
    )

    container = migration_adapter.MigrationContainer()
    migration_adapter.register_migration_services(container)

    adapter = container.get("analytics_service")
    expected = client.get("/v1/analytics/dashboard-summary").json()
    assert adapter.get_dashboard_summary() == expected
