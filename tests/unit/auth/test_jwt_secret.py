from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import time
import types

import pytest

SRC_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard"
    / "src"
    / "services"
    / "security"
    / "jwt_service.py"
)


def load_jwt_service(monkeypatch):
    """Load jwt_service with secret coming from JWT_SECRET_KEY."""
    spec = importlib.util.spec_from_file_location("jwt_service", SRC_PATH)
    module = importlib.util.module_from_spec(spec)

    config_mod = types.ModuleType("yosai_intel_dashboard.src.infrastructure.config")
    config_mod.get_app_config = lambda: types.SimpleNamespace(jwt_secret_path="env")
    sys.modules["yosai_intel_dashboard.src.infrastructure.config"] = config_mod

    def get_secret(_: str) -> str:
        key = os.getenv("JWT_SECRET_KEY")
        if not key:
            raise RuntimeError("JWT_SECRET_KEY not set")
        return key

    secrets_mod = types.ModuleType("yosai_intel_dashboard.src.services.common.secrets")
    secrets_mod.get_secret = get_secret
    secrets_mod.invalidate_secret = lambda key=None: None
    sys.modules["yosai_intel_dashboard.src.services.common.secrets"] = secrets_mod
    spec.loader.exec_module(module)
    return module


def test_startup_requires_secret(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    svc = load_jwt_service(monkeypatch)
    with pytest.raises(RuntimeError):
        svc.jwt_secret()


def test_token_roundtrip(monkeypatch):
    secret = os.urandom(16).hex()
    monkeypatch.setenv("JWT_SECRET_KEY", secret)
    svc = load_jwt_service(monkeypatch)
    now = int(time.time())
    monkeypatch.setattr(svc.time, "time", lambda: now)
    token = svc.generate_service_jwt("svc", expires_in=5)
    claims = svc.verify_service_jwt(token)
    assert claims == {"iss": "svc", "iat": now, "exp": now + 5}


def test_invalid_tokens_rejected(monkeypatch):
    secret = os.urandom(16).hex()
    monkeypatch.setenv("JWT_SECRET_KEY", secret)
    svc = load_jwt_service(monkeypatch)
    now = int(time.time())
    monkeypatch.setattr(svc.time, "time", lambda: now)
    token = svc.generate_service_jwt("svc", expires_in=1)
    tampered = token + "xyz"
    assert svc.verify_service_jwt(tampered) is None
    monkeypatch.setattr(svc.time, "time", lambda: now + 2)
    assert svc.verify_service_jwt(token) is None
