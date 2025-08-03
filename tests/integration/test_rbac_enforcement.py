import importlib.util
import pytest
from flask import Flask

# Import RBAC decorators directly from source file to avoid package side effects
spec = importlib.util.spec_from_file_location(
    "core.rbac", "yosai_intel_dashboard/src/core/rbac.py"
)
rbac = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(rbac)
require_role = rbac.require_role
require_permission = rbac.require_permission


class StubRBACService:
    def __init__(self, roles_map, perms_map):
        self.roles_map = roles_map
        self.perms_map = perms_map

    async def has_role(self, user_id, role):
        return role in self.roles_map.get(user_id, [])

    async def has_permission(self, user_id, perm):
        return perm in self.perms_map.get(user_id, [])


@pytest.fixture
def rbac_service():
    roles = {"admin": ["admin"], "editor": []}
    perms = {"admin": ["edit"], "editor": ["edit"], "viewer": []}
    return StubRBACService(roles, perms)


@pytest.fixture
def app(rbac_service):
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["RBAC_SERVICE"] = rbac_service

    @app.route("/admin")
    @require_role("admin")
    def admin_view():
        return "admin"

    @app.route("/edit")
    @require_permission("edit")
    def edit_view():
        return "edit"

    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    def _login(user_id):
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
    return _login


@pytest.mark.integration
@pytest.mark.parametrize(
    "user,path,expected",
    [
        ("admin", "/admin", 200),
        ("editor", "/admin", 403),
        ("editor", "/edit", 200),
        ("viewer", "/edit", 403),
        ("admin", "/edit", 200),
    ],
)
def test_rbac_enforcement(client, login, user, path, expected):
    login(user)
    resp = client.get(path)
    assert resp.status_code == expected
