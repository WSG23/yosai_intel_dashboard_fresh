from __future__ import annotations

import importlib
import os
import sys
import types
from pathlib import Path

import pyotp
import pytest
from flask import Flask, redirect

from tests.import_helpers import safe_import

# Ensure package path for yosai_intel_dashboard
safe_import("yosai_intel_dashboard", types.ModuleType("yosai_intel_dashboard"))
sys.modules["yosai_intel_dashboard"].__path__ = [
    str(Path(__file__).resolve().parents[1] / "yosai_intel_dashboard")
]

# Provide minimal config stubs to satisfy imports
config_stub = types.ModuleType("config_stub")
config_stub.get_cache_config = lambda: types.SimpleNamespace(jwks_ttl=60)
config_stub.get_security_config = lambda: types.SimpleNamespace(
    session_timeout=3600, session_timeout_by_role={}
)
sys.modules["yosai_intel_dashboard.src.infrastructure.config"] = config_stub

# Stub for database manager module expected by other imports
db_manager_stub = types.ModuleType("db_manager")
db_manager_stub.DatabaseManager = object
db_manager_stub.MockConnection = object
sys.modules["yosai_intel_dashboard.src.infrastructure.config.database_manager"] = (
    db_manager_stub
)

# Prevent heavy query optimizer imports
sys.modules["yosai_intel_dashboard.src.services.query_optimizer"] = types.ModuleType(
    "query_optimizer"
)

# Stub cache manager to avoid additional config imports
cache_manager_stub = types.ModuleType("cache_manager")
cache_manager_stub.CacheConfig = object
sys.modules["yosai_intel_dashboard.src.infrastructure.cache.cache_manager"] = (
    cache_manager_stub
)

# Stub authlib OAuth class to avoid external dependencies
authlib_flask_stub = types.ModuleType("authlib.integrations.flask_client")


class OAuthStub:
    def init_app(self, app):
        return None

    def register(self, *a, **k):
        return object()


authlib_flask_stub.OAuth = OAuthStub
sys.modules["authlib"] = types.ModuleType("authlib")
sys.modules["authlib.integrations"] = types.ModuleType("authlib.integrations")
sys.modules["authlib.integrations.flask_client"] = authlib_flask_stub

# Patch werkzeug.urls for compatibility
werkzeug_urls = importlib.import_module("werkzeug.urls")
if not hasattr(werkzeug_urls, "url_decode"):
    werkzeug_urls.url_decode = lambda *a, **k: {}
if not hasattr(werkzeug_urls, "url_encode"):
    werkzeug_urls.url_encode = lambda *a, **k: ""

from yosai_intel_dashboard.src.core import auth  # noqa: E402
from yosai_intel_dashboard.src.core.session_store import (  # noqa: E402
    InMemorySessionStore,
)
from yosai_intel_dashboard.src.security.roles import require_permission  # noqa: E402


@pytest.fixture
def auth_app(monkeypatch):
    """Create Flask app with stubbed Auth0 integration."""

    mfa_secret = pyotp.random_base32()
    auth0_client_secret = os.urandom(16).hex()
    jwt_secret = os.urandom(16).hex()

    class DummySecretsManager:
        def get(self, key):
            return {
                "AUTH0_CLIENT_ID": "cid",
                "AUTH0_CLIENT_SECRET": auth0_client_secret,
                "AUTH0_DOMAIN": "example.com",
                "AUTH0_AUDIENCE": "https://api.example.com",
                "JWT_SECRET": jwt_secret,
                "MFA_SECRET": mfa_secret,
            }.get(key)

    monkeypatch.setattr(auth, "SecretsManager", DummySecretsManager)
    monkeypatch.setattr(auth, "session_store", InMemorySessionStore())
    monkeypatch.setattr(auth, "_apply_session_timeout", lambda user: None)

    class DummyAuth0:
        def authorize_redirect(self, redirect_uri=None, audience=None, **kwargs):
            return redirect("/callback?code=fake")

        def authorize_access_token(self, **kwargs):
            return {"id_token": "dummy"}

    class DummyOAuth:
        def init_app(self, app):
            return None

        def register(self, name, **kwargs):
            return DummyAuth0()

    monkeypatch.setattr(auth, "oauth", DummyOAuth())

    monkeypatch.setattr(
        auth,
        "_decode_jwt",
        lambda token, domain, audience, client_id: {
            "sub": "user123",
            "name": "Test User",
            "email": "test@example.com",
            "https://yosai-intel.io/roles": ["admin"],
        },
    )

    app = Flask(__name__)
    app.secret_key = os.urandom(16).hex()
    auth.init_auth(app)

    @app.route("/protected")
    @auth.login_required
    def protected():
        return "ok"

    @app.route("/admin")
    @auth.login_required
    @auth.mfa_required
    def admin():
        return "admin"

    @app.route("/need-perm")
    @auth.login_required
    @require_permission("admin:read")
    def need_perm():
        return "perm"

    return app


@pytest.mark.integration
def test_auth_login_flow(auth_app) -> None:
    """User can login and access protected endpoint."""

    client = auth_app.test_client()

    resp = client.get("/login")
    assert resp.status_code == 302

    resp = client.get("/callback?code=fake")
    assert resp.status_code == 302

    with client.session_transaction() as sess:
        assert sess["user_id"] == "user123"
        assert sess["roles"] == ["admin"]

    resp = client.get("/protected")
    assert resp.status_code == 200
    assert resp.data == b"ok"


@pytest.mark.integration
def test_token_refresh(auth_app) -> None:
    client = auth_app.test_client()
    client.get("/login")
    client.get("/callback?code=fake")
    resp = client.get("/token")
    first = resp.get_json()["access_token"]
    resp = client.get("/refresh")
    second = resp.get_json()["access_token"]
    assert first != second


@pytest.mark.integration
def test_role_enforcement(auth_app) -> None:
    client = auth_app.test_client()
    client.get("/login")
    client.get("/callback?code=fake")
    resp = client.get("/need-perm")
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        sess["permissions"] = []
    resp = client.get("/need-perm")
    assert resp.status_code == 403


@pytest.mark.integration
def test_mfa_flow(auth_app) -> None:
    client = auth_app.test_client()
    client.get("/login")
    client.get("/callback?code=fake")
    resp = client.get("/admin")
    assert resp.status_code == 302
    code = pyotp.TOTP(mfa_secret).now()
    client.get(f"/mfa/verify?code={code}")
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert resp.data == b"admin"


@pytest.mark.integration
def test_cookie_attributes(auth_app) -> None:
    client = auth_app.test_client()
    client.get("/login")
    resp = client.get("/callback?code=fake")
    cookie = resp.headers.get("Set-Cookie")
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=Strict" in cookie
