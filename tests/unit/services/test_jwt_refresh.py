from __future__ import annotations

import importlib
import os
import sys
import types
import time

from yosai_intel_dashboard.src.core.imports.resolver import safe_import


def load_service(monkeypatch, secret: str | None = None):
    if secret is None:
        secret = os.urandom(16).hex()
    secrets_mod = types.ModuleType(
        "yosai_intel_dashboard.src.services.common.secrets"
    )
    secrets_mod.get_secret = lambda key: secret
    secrets_mod.invalidate_secret = lambda key=None: None
    safe_import(
        "yosai_intel_dashboard.src.services.common.secrets", secrets_mod
    )
    config_mod = types.ModuleType(
        "yosai_intel_dashboard.src.infrastructure.config"
    )
    config_mod.get_app_config = lambda: types.SimpleNamespace(jwt_secret_path="ignored")
    safe_import(
        "yosai_intel_dashboard.src.infrastructure.config", config_mod
    )
    module_name = "yosai_intel_dashboard.src.services.security.jwt_service"
    if module_name in sys.modules:
        module = sys.modules[module_name]
        importlib.reload(module)
    else:
        module = importlib.import_module(module_name)
    return module


def test_refresh_access_token_invalid(monkeypatch):
    svc = load_service(monkeypatch)
    now = int(time.time())
    monkeypatch.setattr(svc.time, "time", lambda: now)
    _, refresh = svc.generate_token_pair(
        "svc", access_expires_in=10, refresh_expires_in=1
    )
    monkeypatch.setattr(svc.time, "time", lambda: now + 2)
    assert svc.refresh_access_token(refresh) is None
