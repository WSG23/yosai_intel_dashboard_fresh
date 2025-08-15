from __future__ import annotations

import json
import sys
import types

from flask import Flask


def import_auth(monkeypatch):
    class DummyOAuth:
        def init_app(self, app):
            pass

        def register(self, *a, **k):
            return types.SimpleNamespace(
                authorize_redirect=lambda **kw: None,
                authorize_access_token=lambda **kw: {},
            )

    stub = DummyOAuth
    monkeypatch.setitem(
        sys.modules,
        "authlib",
        types.SimpleNamespace(
            integrations=types.SimpleNamespace(
                flask_client=types.SimpleNamespace(OAuth=stub)
            )
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "authlib.integrations",
        types.SimpleNamespace(flask_client=types.SimpleNamespace(OAuth=stub)),
    )
    monkeypatch.setitem(
        sys.modules,
        "authlib.integrations.flask_client",
        types.SimpleNamespace(OAuth=stub),
    )

    cfg_stub = types.SimpleNamespace(
        get_cache_config=lambda: types.SimpleNamespace(jwks_ttl=60),
        get_security_config=lambda: types.SimpleNamespace(
            session_timeout=10, session_timeout_by_role={}
        ),
    )
    roles_stub = types.SimpleNamespace(get_permissions_for_roles=lambda roles: [])
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.infrastructure.config",
        cfg_stub,
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.security.roles",
        roles_stub,
    )

    from yosai_intel_dashboard.src.core import auth

    return auth


def test_get_jwks_caches(monkeypatch):
    auth = import_auth(monkeypatch)
    jwks = {"keys": [{"kid": "abc"}]}

    def fake_urlopen(url, timeout):
        fake_urlopen.count += 1

        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                pass

            def read(self):
                return json.dumps(jwks).encode()

        return Resp()

    fake_urlopen.count = 0
    monkeypatch.setattr(auth, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        auth, "get_cache_config", lambda: types.SimpleNamespace(jwks_ttl=60)
    )
    monkeypatch.setattr(auth, "_jwks_cache", {})

    first = auth._get_jwks("example.com")
    second = auth._get_jwks("example.com")

    assert first == jwks
    assert second == jwks
    assert fake_urlopen.count == 1


def test_decode_jwt_selects_key(monkeypatch):
    auth = import_auth(monkeypatch)
    monkeypatch.setattr(
        auth, "_get_jwks", lambda domain: {"keys": [{"kid": "abc"}, {"kid": "def"}]}
    )

    captured = {}

    def fake_get_header(token):
        return {"kid": "abc"}

    def fake_decode(token, key, algorithms, audience, issuer):
        captured["key"] = key
        captured["audience"] = audience
        captured["issuer"] = issuer
        return {"sub": "1"}

    monkeypatch.setattr(auth.jwt, "get_unverified_header", fake_get_header)
    monkeypatch.setattr(auth.jwt, "decode", fake_decode)

    result = auth._decode_jwt("token", "domain", "aud", "client")

    assert result == {"sub": "1"}
    assert captured["key"]["kid"] == "abc"
    assert captured["audience"] == "aud"
    assert captured["issuer"] == "https://domain/"


def test_determine_and_apply_session_timeout(monkeypatch):
    auth = import_auth(monkeypatch)
    cfg = types.SimpleNamespace(
        session_timeout=10, session_timeout_by_role={"admin": 20}
    )
    monkeypatch.setattr(auth, "get_security_config", lambda: cfg)

    assert auth._determine_session_timeout(["admin", "user"]) == 20
    assert auth._determine_session_timeout(["user"]) == 10

    app = Flask(__name__)
    app.secret_key = "x"
    with app.test_request_context():
        user = auth.User("1", "n", "e", ["user"])
        monkeypatch.setattr(auth, "_determine_session_timeout", lambda roles: 42)
        auth._apply_session_timeout(user)
        assert auth.session.permanent
        assert auth.current_app.permanent_session_lifetime.total_seconds() == 42


def test_role_required_and_mfa_required(monkeypatch):
    auth = import_auth(monkeypatch)
    app = Flask(__name__)
    app.secret_key = "x"
    monkeypatch.setattr(auth, "url_for", lambda endpoint: "/mfa")

    @auth.role_required("admin")
    def protected_role():
        return "ok"

    @auth.mfa_required
    def protected_mfa():
        return "ok"

    with app.test_request_context():
        auth.session["roles"] = ["admin"]
        assert protected_role() == "ok"
        auth.session["roles"] = []
        assert protected_role() == ("Forbidden", 403)

        auth.session["mfa_verified"] = False
        resp = protected_mfa()
        assert resp.status_code == 302
        assert resp.location.endswith("/mfa")
        auth.session["mfa_verified"] = True
        assert protected_mfa() == "ok"

