"""Authorization tests for API endpoints."""

import os
import sys
import types
from pathlib import Path
from typing import Any, cast

# Configure environment and stub heavy dependencies before importing the app.
os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")

secrets_stub = cast(
    Any, types.ModuleType("yosai_intel_dashboard.src.services.common.secrets")
)
secrets_stub.get_secret = lambda key: "test"
secrets_stub.invalidate_secret = lambda key=None: None
sys.modules["yosai_intel_dashboard.src.services.common.secrets"] = secrets_stub
sys.modules["graphene"] = cast(Any, None)
sys.modules["fastapi.graphql"] = cast(Any, None)
usv_stub = cast(
    Any,
    types.ModuleType(
        "yosai_intel_dashboard.src.infrastructure.security.unicode_security_validator"
    ),
)
usv_stub.UnicodeSecurityValidator = object
sys.modules[
    "yosai_intel_dashboard.src.infrastructure.security.unicode_security_validator"
] = usv_stub

jwt_stub = cast(
    Any, types.ModuleType("yosai_intel_dashboard.src.services.security.jwt_service")
)


class TokenValidationError(Exception):
    pass


jwt_stub.TokenValidationError = TokenValidationError
jwt_stub.generate_refresh_jwt = lambda *a, **k: ""
jwt_stub.generate_service_jwt = lambda *a, **k: ""
jwt_stub.generate_token_pair = lambda *a, **k: ("", "")
jwt_stub.invalidate_jwt_secret_cache = lambda *a, **k: None
jwt_stub.refresh_access_token = lambda *a, **k: ""
jwt_stub.verify_refresh_jwt = lambda *a, **k: {}
jwt_stub.verify_service_jwt = lambda *a, **k: {}
sys.modules["yosai_intel_dashboard.src.services.security.jwt_service"] = jwt_stub

# Ensure repository root is on the import path.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from fastapi import Depends as _Depends  # noqa: E402
import builtins  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

setattr(builtins, "Depends", _Depends)
from services.api.main import app  # noqa: E402


client = TestClient(app)


def test_echo_rejects_missing_role() -> None:
    """Requests without roles should be rejected."""
    resp = client.post("/api/v1/echo", json={"message": "hi"})
    assert resp.status_code in (401, 403)  # nosec B101


def test_echo_rejects_incorrect_role() -> None:
    """Requests with incorrect roles should be rejected."""
    resp = client.post(
        "/api/v1/echo", json={"message": "hi"}, headers={"X-Roles": "user"}
    )
    assert resp.status_code in (401, 403)  # nosec B101


def test_echo_allows_admin_role() -> None:
    """Requests with the admin role should succeed."""
    resp = client.post(
        "/api/v1/echo", json={"message": "hi"}, headers={"X-Roles": "admin"}
    )
    assert resp.status_code == 200  # nosec B101
    assert resp.json() == {"message": "hi"}  # nosec B101
