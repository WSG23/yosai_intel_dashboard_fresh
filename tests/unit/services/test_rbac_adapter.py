from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from typing import Any, cast

import jwt
from flask import Flask

os.environ.setdefault("VAULT_ADDR", "http://localhost")
os.environ.setdefault("VAULT_TOKEN", "test")

vault_mod = types.ModuleType("yosai_intel_dashboard.src.services.common.vault_client")
vault_mod.VaultClient = lambda *a, **k: None  # type: ignore[attr-defined]
sys.modules["yosai_intel_dashboard.src.services.common.vault_client"] = vault_mod

services_pkg = types.ModuleType("yosai_intel_dashboard.src.services")
services_pkg.__path__ = [
    str(
        Path(__file__).resolve().parents[2]
        / "yosai_intel_dashboard"
        / "src"
        / "services"
    )
]
sys.modules["yosai_intel_dashboard.src.services"] = services_pkg

jwt_service_stub = types.ModuleType(
    "yosai_intel_dashboard.src.services.security.jwt_service"
)


class TokenValidationError(Exception):
    pass


def verify_service_jwt(token: str, **_: object) -> dict[str, Any]:
    import jwt as _jwt

    return cast(dict[str, Any], _jwt.decode(token, "secret", algorithms=["HS256"]))


jwt_service_stub.TokenValidationError = TokenValidationError  # type: ignore[attr-defined]  # noqa: E501
jwt_service_stub.verify_service_jwt = verify_service_jwt  # type: ignore[attr-defined]
jwt_service_stub.generate_refresh_jwt = lambda *a, **k: ""  # type: ignore[attr-defined]
jwt_service_stub.generate_service_jwt = lambda *a, **k: ""  # type: ignore[attr-defined]
jwt_service_stub.generate_token_pair = lambda *a, **k: ("", "")  # type: ignore[attr-defined]  # noqa: E501
jwt_service_stub.invalidate_jwt_secret_cache = lambda *a, **k: None  # type: ignore[attr-defined]  # noqa: E501
jwt_service_stub.refresh_access_token = lambda *a, **k: ""  # type: ignore[attr-defined]
jwt_service_stub.verify_refresh_jwt = lambda *a, **k: {}  # type: ignore[attr-defined]
sys.modules["yosai_intel_dashboard.src.services.security.jwt_service"] = (
    jwt_service_stub
)

from yosai_intel_dashboard.src.services.security import require_permission  # noqa: E402
from yosai_intel_dashboard.src.services.security import rbac_adapter  # noqa: E402


def _token(role: str) -> str:
    payload = {"sub": "u1", "role": role}
    return cast(str, jwt.encode(payload, "secret", algorithm="HS256"))


def _setup_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "test"

    @app.route("/secure")  # type: ignore[misc]
    @require_permission("analytics:write")
    def secure() -> str:
        return "ok"

    return app


def test_has_permission_allows() -> None:
    assert rbac_adapter.has_permission("analyst", "analytics:write")
    assert not rbac_adapter.has_permission("viewer", "analytics:write")


def test_require_permission_decorator(monkeypatch: Any) -> None:
    from yosai_intel_dashboard.src.services import security as sec

    monkeypatch.setattr(sec, "verify_behavioral_biometrics", lambda req: True)

    app = _setup_app()
    client = app.test_client()

    resp = client.get(
        "/secure", headers={"Authorization": f"Bearer {_token('analyst')}"}
    )
    assert resp.status_code == 200

    resp = client.get(
        "/secure", headers={"Authorization": f"Bearer {_token('viewer')}"}
    )
    assert resp.status_code == 403
