from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

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


@pytest.fixture
def auth_app(monkeypatch):
    """Create Flask app with stubbed Auth0 integration."""

    class DummySecretsManager:
        def get(self, key):
            return {
                "AUTH0_CLIENT_ID": "cid",
                "AUTH0_CLIENT_SECRET": "csecret",
                "AUTH0_DOMAIN": "example.com",
                "AUTH0_AUDIENCE": "https://api.example.com",
            }.get(key)

    monkeypatch.setattr(auth, "SecretsManager", DummySecretsManager)
    monkeypatch.setattr(auth, "_users", {})
    monkeypatch.setattr(auth, "_apply_session_timeout", lambda user: None)

    class DummyAuth0:
        def authorize_redirect(self, redirect_uri=None, audience=None):
            return redirect("/callback?code=fake")

        def authorize_access_token(self):
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
    app.secret_key = "testing"
    auth.init_auth(app)

    @app.route("/protected")
    @auth.login_required
    def protected():
        return "ok"

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
