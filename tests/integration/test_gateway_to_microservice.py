import importlib.util
import os
import pathlib
import sys
import types
import time

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# Stub lightweight services package for microservice import
SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_stub)


class DummyAnalytics:
    def get_dashboard_summary(self) -> dict:
        return {"status": "ok"}

    def get_access_patterns_analysis(self, days: int = 7) -> dict:
        return {"days": days}


analytics_stub = types.ModuleType("services.analytics_service")
analytics_stub.create_analytics_service = lambda: DummyAnalytics()
sys.modules["services.analytics_service"] = analytics_stub

app_spec = importlib.util.spec_from_file_location(
    "services.analytics_microservice.app",
    SERVICES_PATH / "analytics_microservice" / "app.py",
)
app_module = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(app_module)


@pytest.mark.integration
def test_requests_without_valid_token_return_401(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test")
    client = TestClient(app_module.app)

    # No Authorization header
    resp = client.post("/api/v1/analytics/get_dashboard_summary")
    assert resp.status_code == 401

    # Expired token
    bad_token = jwt.encode(
        {"sub": "svc", "exp": int(time.time()) - 1}, "test", algorithm="HS256"
    )
    resp = client.post(
        "/api/v1/analytics/get_dashboard_summary",
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert resp.status_code == 401

    # Valid token succeeds
    good_token = jwt.encode(
        {"sub": "svc", "exp": int(time.time()) + 60}, "test", algorithm="HS256"
    )
    resp = client.post(
        "/api/v1/analytics/get_dashboard_summary",
        headers={"Authorization": f"Bearer {good_token}"},
    )
    assert resp.status_code == 200
