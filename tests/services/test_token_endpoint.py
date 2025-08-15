from __future__ import annotations

import sys
import types
from flask import Flask
from shared.errors.types import ErrorCode

# Stub security module to avoid external dependencies
security_stub = types.ModuleType("yosai_intel_dashboard.src.services.security")
security_stub.refresh_access_token = lambda token: "token"
sys.modules.setdefault("yosai_intel_dashboard.src.services.security", security_stub)

# Stub monitoring dependency to avoid importing prometheus_client
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.monitoring.error_budget",
    types.SimpleNamespace(record_error=lambda *a, **k: None),
)

# Stub error handling to avoid importing heavy dependencies
error_handling_stub = types.ModuleType(
    "yosai_intel_dashboard.src.error_handling"
)
error_handling_stub.ErrorCategory = types.SimpleNamespace(
    UNAUTHORIZED="unauthorized"
)
class _Handler:
    def handle(self, exc, category):
        return {"code": str(category), "message": str(exc)}

error_handling_stub.ErrorHandler = _Handler

def _api_error_response(exc, category, handler=None):
    return {"code": str(category), "message": str(exc)}, 401

error_handling_stub.api_error_response = _api_error_response
sys.modules.setdefault(
    "yosai_intel_dashboard.src.error_handling", error_handling_stub
)

# Stub pydantic validators to no-ops
decorators_stub = types.ModuleType(
    "yosai_intel_dashboard.src.utils.pydantic_decorators"
)

def _validate_input(model):
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import request

            data = request.get_json() or {}
            payload = types.SimpleNamespace(**data)
            return func(payload)
        return wrapper
    return decorator

decorators_stub.validate_input = _validate_input
decorators_stub.validate_output = lambda model: (lambda func: func)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.utils.pydantic_decorators", decorators_stub
)

# Stub error mapping to avoid importing yosai_framework
sys.modules.setdefault(
    "yosai_framework.errors",
    types.SimpleNamespace(
        CODE_TO_STATUS={
            ErrorCode.INVALID_INPUT: 400,
            ErrorCode.UNAUTHORIZED: 401,
            ErrorCode.INTERNAL: 500,
        }
    ),
)

from yosai_intel_dashboard.src.services import token_endpoint


def _make_client(monkeypatch, token):
    monkeypatch.setattr(token_endpoint, "refresh_access_token", lambda refresh: token)
    app = Flask(__name__)
    app.register_blueprint(token_endpoint.create_token_blueprint())
    return app.test_client()


def test_refresh_token_success(monkeypatch):
    client = _make_client(monkeypatch, "new-token")
    resp = client.post("/v1/token/refresh", json={"refresh_token": "old"})
    assert resp.status_code == 200
    assert resp.get_json() == {"access_token": "new-token"}


def test_refresh_token_invalid(monkeypatch):
    client = _make_client(monkeypatch, None)
    resp = client.post("/v1/token/refresh", json={"refresh_token": "bad"})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["code"] == "unauthorized"
    assert data["message"] == "invalid refresh token"
