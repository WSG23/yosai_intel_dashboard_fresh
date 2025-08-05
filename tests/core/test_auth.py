from __future__ import annotations

import json

from flask import Flask, session

from yosai_intel_dashboard.src.core import auth as auth_module


class DummyResp:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        from io import StringIO

        return StringIO(json.dumps(self.data))

    def __exit__(self, exc_type, exc, tb):
        return False


def test_get_jwks_caches(monkeypatch):
    calls = {"count": 0}
    jwks = {"keys": []}

    def fake_urlopen(url, timeout=None):
        calls["count"] += 1
        return DummyResp(jwks)

    class DummyConfig:
        jwks_ttl = 10

    monkeypatch.setattr(auth_module, "urlopen", fake_urlopen)
    monkeypatch.setattr(auth_module, "get_cache_config", lambda: DummyConfig())
    monkeypatch.setattr(auth_module, "_jwks_cache", {}, raising=False)
    first = auth_module._get_jwks("example.com")
    second = auth_module._get_jwks("example.com")
    assert first == jwks
    assert second == jwks
    assert calls["count"] == 1


def test_role_required(monkeypatch):
    app = Flask(__name__)
    app.secret_key = "test"
    with app.test_request_context("/"):
        session["roles"] = ["admin"]

        @auth_module.role_required("admin")
        def view():
            return "ok", 200

        assert view() == ("ok", 200)

    with app.test_request_context("/"):
        session["roles"] = []

        @auth_module.role_required("admin")
        def view2():
            return "ok", 200

        assert view2() == ("Forbidden", 403)


def test_mfa_required(monkeypatch):
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(auth_module.auth_bp)

    @auth_module.mfa_required
    def view():
        return "ok", 200

    with app.test_request_context("/"):
        session.clear()
        resp = view()
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/mfa")

    with app.test_request_context("/"):
        session["mfa_verified"] = True
        assert view() == ("ok", 200)
