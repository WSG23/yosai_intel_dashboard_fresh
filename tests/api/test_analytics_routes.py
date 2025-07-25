import logging
import sys
import types
from dataclasses import dataclass

import pytest
from flask import Flask, jsonify
from flask_wtf.csrf import CSRFProtect, generate_csrf


def _create_app(monkeypatch):
    class DummyCacheManager:
        def __init__(self, *a, **k):
            pass

        async def start(self):
            pass

    class DummyAnalyticsService:
        def __init__(self, *a, **k):
            pass

        async def get_analytics_summary(self, facility, date_range):
            from yosai_intel_dashboard.src.adapters.api.analytics_endpoints import (
                MOCK_DATA,
            )

            return MOCK_DATA

    monkeypatch.setitem(
        sys.modules,
        "core.advanced_cache",
        types.SimpleNamespace(AdvancedCacheManager=DummyCacheManager),
    )

    @dataclass
    class DummyCacheConfig:
        timeout_seconds: int = 300

    monkeypatch.setitem(
        sys.modules,
        "config.base",
        types.SimpleNamespace(CacheConfig=DummyCacheConfig),
    )
    monkeypatch.setitem(
        sys.modules,
        "core.rbac",
        types.SimpleNamespace(RBACService=object, create_rbac_service=lambda: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "services.cached_analytics",
        types.SimpleNamespace(CachedAnalyticsService=DummyAnalyticsService),
    )

    monkeypatch.setitem(
        sys.modules,
        "services.security",
        types.SimpleNamespace(
            require_token=lambda f: f, require_permission=lambda p: (lambda f: f)
        ),
    )

    from yosai_intel_dashboard.src.adapters.api.analytics_endpoints import (
        register_analytics_blueprints,
    )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-key"
    CSRFProtect(app)

    register_analytics_blueprints(app)

    @app.route("/v1/csrf-token")
    def csrf_token():
        return jsonify({"csrf_token": generate_csrf()})

    return app


def test_patterns_returns_json(monkeypatch):
    app = _create_app(monkeypatch)
    client = app.test_client()
    resp = client.get("/api/v1/analytics/patterns")
    assert resp.status_code == 200
    assert resp.is_json
    assert "status" in resp.get_json()


def test_csrf_token_endpoint(monkeypatch):
    app = _create_app(monkeypatch)
    client = app.test_client()
    resp = client.get("/v1/csrf-token")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "csrf_token" in body
    assert "HttpOnly" in resp.headers.get("Set-Cookie", "")
