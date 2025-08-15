from __future__ import annotations

import sys
import types
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Stub security module to avoid external dependencies
security_stub = types.ModuleType("yosai_intel_dashboard.src.services.security")
security_stub.refresh_access_token = lambda token: "token"
sys.modules.setdefault("yosai_intel_dashboard.src.services.security", security_stub)

# Stub monitoring dependency to avoid importing prometheus_client
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.monitoring.error_budget",
    types.SimpleNamespace(record_error=lambda *a, **k: None),
)

from yosai_intel_dashboard.src.services import token_endpoint


def _make_client(monkeypatch, token):
    monkeypatch.setattr(token_endpoint, "refresh_access_token", lambda refresh: token)
    app = FastAPI()
    app.include_router(token_endpoint.create_token_router())
    return TestClient(app)


def test_refresh_token_success(monkeypatch):
    client = _make_client(monkeypatch, "new-token")
    resp = client.post("/v1/token/refresh", json={"refresh_token": "old"})
    assert resp.status_code == 200
    assert resp.json() == {"access_token": "new-token"}


def test_refresh_token_invalid(monkeypatch):
    client = _make_client(monkeypatch, None)
    resp = client.post("/v1/token/refresh", json={"refresh_token": "bad"})
    assert resp.status_code == 401
    data = resp.json()
    assert data["code"] == "unauthorized"
    assert data["message"] == "invalid refresh token"
