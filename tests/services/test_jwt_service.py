import importlib
import pathlib
import sys
import time
import types

import pytest


SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"


def load_jwt_service(monkeypatch, secret: str = "secret"):
    """Import ``jwt_service`` with the given secret configured."""

    services_mod = sys.modules.get("services")
    if services_mod is None:
        services_mod = types.ModuleType("services")
        sys.modules["services"] = services_mod
    services_mod.__path__ = [str(SERVICES_PATH)]

    security_mod = sys.modules.get("services.security")
    if security_mod is None:
        security_mod = types.ModuleType("services.security")
        sys.modules["services.security"] = security_mod
    security_mod.__path__ = [str(SERVICES_PATH / "security")]

    secrets_mod = types.ModuleType("services.common.secrets")
    secrets_mod.get_secret = lambda key: secret
    secrets_mod.invalidate_secret = lambda key=None: None
    monkeypatch.setitem(sys.modules, "services.common.secrets", secrets_mod)

    module_name = "services.security.jwt_service"
    if module_name in sys.modules:
        module = sys.modules[module_name]
        importlib.reload(module)
    else:
        module = importlib.import_module(module_name)
    return module


def test_token_valid_when_issued(monkeypatch):
    svc = load_jwt_service(monkeypatch, "top-secret")
    now = int(time.time())
    monkeypatch.setattr(svc.time, "time", lambda: now)
    token = svc.generate_service_jwt("analytics", expires_in=30)
    claims = svc.verify_service_jwt(token)
    assert claims == {"iss": "analytics", "iat": now, "exp": now + 30}


def test_expired_token_returns_none(monkeypatch):
    svc = load_jwt_service(monkeypatch, "top-secret")
    now = int(time.time()) - 100
    monkeypatch.setattr(svc.time, "time", lambda: now)
    token = svc.generate_service_jwt("svc", expires_in=1)
    assert svc.verify_service_jwt(token) is None


def test_invalid_signature_returns_none(monkeypatch):
    svc = load_jwt_service(monkeypatch, "secret-one")
    now = int(time.time())
    monkeypatch.setattr(svc.time, "time", lambda: now)
    token = svc.generate_service_jwt("svc", expires_in=30)
    # Change the secret used for verification
    secrets_mod = sys.modules["services.common.secrets"]
    secrets_mod.get_secret = lambda key: "secret-two"
    assert svc.verify_service_jwt(token) is None
