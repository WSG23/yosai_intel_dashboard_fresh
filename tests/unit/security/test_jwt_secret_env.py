import importlib.util
import pathlib
import sys
import types

import pytest

SRC_PATH = pathlib.Path(__file__).resolve().parents[2] / "yosai_intel_dashboard" / "src" / "services" / "security" / "jwt_service.py"


def load_jwt_service(secret_path: str = "vault/path"):
    spec = importlib.util.spec_from_file_location("jwt_service", SRC_PATH)
    module = importlib.util.module_from_spec(spec)
    secrets_mod = types.ModuleType("yosai_intel_dashboard.src.services.common.secrets")
    called = {}

    def fake_get_secret(key: str) -> str:
        called["key"] = key
        return "top"

    secrets_mod.get_secret = fake_get_secret
    secrets_mod.invalidate_secret = lambda key=None: None
    sys.modules["yosai_intel_dashboard.src.services.common.secrets"] = secrets_mod
    spec.loader.exec_module(module)
    return module, called


def test_read_jwt_secret_uses_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_PATH", "vault/custom")
    module, called = load_jwt_service()
    assert module._read_jwt_secret() == "top"
    assert called["key"] == "vault/custom"


def test_read_jwt_secret_requires_env(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_PATH", raising=False)
    module, _ = load_jwt_service()
    with pytest.raises(RuntimeError):
        module._read_jwt_secret()
