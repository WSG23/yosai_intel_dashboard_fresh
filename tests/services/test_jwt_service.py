from __future__ import annotations

import importlib
import os
import pathlib
import sys
import time
import types

import pytest

from yosai_intel_dashboard.src.core.imports.resolver import safe_import

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"


def load_jwt_service(monkeypatch, secret: str | None = None):
    """Import ``jwt_service`` with the given secret configured."""

    if secret is None:
        secret = os.urandom(16).hex()

    services_mod = sys.modules.get("services")
    if services_mod is None:
        services_mod = types.ModuleType("services")
        safe_import("services", services_mod)
    services_mod.__path__ = [str(SERVICES_PATH)]

    security_mod = sys.modules.get("services.security")
    if security_mod is None:
        security_mod = types.ModuleType("services.security")
        safe_import("services.security", security_mod)
    security_mod.__path__ = [str(SERVICES_PATH / "security")]

    secrets_mod = types.ModuleType("services.common.secrets")
    secrets_mod.get_secret = lambda key: secret
    secrets_mod.invalidate_secret = lambda key=None: None
    safe_import("services.common.secrets", secrets_mod)

    module_name = "services.security.jwt_service"
    if module_name in sys.modules:
        module = sys.modules[module_name]
        importlib.reload(module)
    else:
        module = importlib.import_module(module_name)
    return module


def test_token_valid_when_issued(monkeypatch):
    svc = load_jwt_service(monkeypatch, os.urandom(16).hex())
    now = int(time.time())
    monkeypatch.setattr(svc.time, "time", lambda: now)
    token = svc.generate_service_jwt("analytics", expires_in=30)
    claims = svc.verify_service_jwt(token)
    assert claims == {
        "iss": "analytics",
        "sub": "analytics",
        "iat": now,
        "exp": now + 30,
    }


def test_expired_token_raises_error(monkeypatch):
    svc = load_jwt_service(monkeypatch, os.urandom(16).hex())
    now = int(time.time()) - 100
    monkeypatch.setattr(svc.time, "time", lambda: now)
    token = svc.generate_service_jwt("svc", expires_in=1)
    with pytest.raises(svc.TokenValidationError) as exc:
        svc.verify_service_jwt(token)
    assert exc.value.code == "token_expired"


def test_invalid_signature_raises_error(monkeypatch):
    svc = load_jwt_service(monkeypatch, os.urandom(16).hex())
    now = int(time.time())
    monkeypatch.setattr(svc.time, "time", lambda: now)
    token = svc.generate_service_jwt("svc", expires_in=30)
    # Change the secret used for verification
    secrets_mod = sys.modules["services.common.secrets"]
    secrets_mod.get_secret = lambda key: "secret-two"
    svc.invalidate_jwt_secret_cache()
    with pytest.raises(svc.TokenValidationError) as exc:
        svc.verify_service_jwt(token)
    assert exc.value.code == "token_invalid"


def test_mismatched_audience(monkeypatch):
    svc = load_jwt_service(monkeypatch, os.urandom(16).hex())
    now = int(time.time())
    monkeypatch.setattr(svc.time, "time", lambda: now)
    token = svc.generate_service_jwt("svc", expires_in=30, audience="expected")
    with pytest.raises(svc.TokenValidationError) as exc:
        svc.verify_service_jwt(token, audience="other")
    assert exc.value.code == "invalid_audience"


def test_refresh_token_flow(monkeypatch):
    svc = load_jwt_service(monkeypatch, os.urandom(16).hex())
    now = int(time.time())
    monkeypatch.setattr(svc.time, "time", lambda: now)
    access, refresh = svc.generate_token_pair(
        "svc", access_expires_in=1, refresh_expires_in=10
    )
    assert svc.verify_service_jwt(access)["iss"] == "svc"
    assert svc.verify_refresh_jwt(refresh)["iss"] == "svc"

    # expire access token
    monkeypatch.setattr(svc.time, "time", lambda: now + 2)
    with pytest.raises(svc.TokenValidationError):
        svc.verify_service_jwt(access)

    new_access = svc.refresh_access_token(refresh, expires_in=5)
    assert new_access is not None
    claims = svc.verify_service_jwt(new_access)
    assert claims["iss"] == "svc"


def test_secret_cached_until_invalidated(monkeypatch):
    secret_one = os.urandom(16).hex()
    svc = load_jwt_service(monkeypatch, secret_one)
    assert svc.jwt_secret() == secret_one

    secrets_mod = sys.modules["services.common.secrets"]
    secret_two = os.urandom(16).hex()
    secrets_mod.get_secret = lambda key: secret_two
    # Still returns cached secret
    assert svc.jwt_secret() == secret_one

    svc.invalidate_jwt_secret_cache()
    assert svc.jwt_secret() == secret_two
