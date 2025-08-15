import sys
import types

import pytest
from httpx import AsyncClient

# Provide a stub secrets module to avoid Vault dependency during import
secrets_stub = types.ModuleType("yosai_intel_dashboard.src.services.common.secrets")
secrets_stub.get_secret = lambda key: "test"
secrets_stub.invalidate_secret = lambda key=None: None
sys.modules["yosai_intel_dashboard.src.services.common.secrets"] = secrets_stub
sys.modules["graphene"] = None
sys.modules["fastapi.graphql"] = None

from services.api.main import app as api_app
from yosai_intel_dashboard.src.services.intel_analysis_service.api.service import (
    app as intel_app,
)


@pytest.mark.anyio
async def test_api_echo_requires_admin_role():
    async with AsyncClient(app=api_app, base_url="http://test") as client:
        resp = await client.post("/api/v1/echo", json={"message": "hi"})
        assert resp.status_code == 403
        resp = await client.post(
            "/api/v1/echo", json={"message": "hi"}, headers={"X-Roles": "admin"}
        )
        assert resp.status_code == 200


@pytest.mark.anyio
async def test_intel_service_requires_analyst_role():
    async with AsyncClient(app=intel_app, base_url="http://test") as client:
        resp = await client.get("/api/v1/status")
        assert resp.status_code == 403
        resp = await client.get("/api/v1/status", headers={"X-Roles": "analyst"})
        assert resp.status_code == 200
