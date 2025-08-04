import asyncio
import importlib.util
import os

import pytest
from flask import Flask, session

# Import core.rbac directly from file to avoid package side effects
spec = importlib.util.spec_from_file_location(
    "core.rbac", "yosai_intel_dashboard/src/core/rbac.py"
)
rbac = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(rbac)
require_role = rbac.require_role
require_permission = rbac.require_permission

SECRET_KEY = os.urandom(16).hex()


class DummyService:
    async def has_role(self, user_id: str, role: str) -> bool:
        return user_id == "u1" and role == "admin"

    async def has_permission(self, user_id: str, perm: str) -> bool:
        return user_id == "u1" and perm == "read"


def test_require_role_async_allows():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["RBAC_SERVICE"] = DummyService()
    with app.test_request_context():
        session["user_id"] = "u1"

        @require_role("admin")
        async def endpoint():
            return "ok"

        assert asyncio.run(endpoint()) == "ok"


def test_require_role_async_forbidden():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["RBAC_SERVICE"] = DummyService()
    with app.test_request_context():
        session["user_id"] = "u1"

        @require_role("user")
        async def endpoint():
            return "ok"

        assert asyncio.run(endpoint()) == ("Forbidden", 403)


def test_require_permission_sync_allows():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["RBAC_SERVICE"] = DummyService()
    with app.test_request_context():
        session["user_id"] = "u1"

        @require_permission("read")
        def endpoint():
            return "ok"

        assert endpoint() == "ok"


def test_require_permission_sync_forbidden():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["RBAC_SERVICE"] = DummyService()
    with app.test_request_context():
        session["user_id"] = "u1"

        @require_permission("write")
        def endpoint():
            return "ok"

        assert endpoint() == ("Forbidden", 403)


def test_require_role_sync_allows():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["RBAC_SERVICE"] = DummyService()
    with app.test_request_context():
        session["user_id"] = "u1"

        @require_role("admin")
        def endpoint():
            return "ok"

        assert endpoint() == "ok"


def test_require_role_sync_forbidden():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["RBAC_SERVICE"] = DummyService()
    with app.test_request_context():
        session["user_id"] = "u1"

        @require_role("user")
        def endpoint():
            return "ok"

        assert endpoint() == ("Forbidden", 403)


def test_require_permission_async_allows():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["RBAC_SERVICE"] = DummyService()
    with app.test_request_context():
        session["user_id"] = "u1"

        @require_permission("read")
        async def endpoint():
            return "ok"

        assert asyncio.run(endpoint()) == "ok"


def test_require_permission_async_forbidden():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["RBAC_SERVICE"] = DummyService()
    with app.test_request_context():
        session["user_id"] = "u1"

        @require_permission("write")
        async def endpoint():
            return "ok"

        assert asyncio.run(endpoint()) == ("Forbidden", 403)


def test_biometric_block_role(monkeypatch):
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["RBAC_SERVICE"] = DummyService()
    with app.test_request_context():
        session["user_id"] = "u1"
        monkeypatch.setattr(rbac, "_verify_behavioral_biometrics", lambda req: False)

        @require_role("admin")
        def endpoint():
            return "ok"

        assert endpoint() == ("Forbidden", 403)


def test_biometric_block_permission(monkeypatch):
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["RBAC_SERVICE"] = DummyService()
    with app.test_request_context():
        session["user_id"] = "u1"
        monkeypatch.setattr(rbac, "_verify_behavioral_biometrics", lambda req: False)

        @require_permission("read")
        def endpoint():
            return "ok"

        assert endpoint() == ("Forbidden", 403)
