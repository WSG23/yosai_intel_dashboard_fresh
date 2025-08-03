import asyncio
import importlib
import importlib.util
import shutil
import sys

import asyncpg
import pytest

# Replace requests stub from tests.config with the real library for testcontainers
sys.modules.pop("requests", None)
requests = importlib.import_module("requests")  # noqa: F401

from testcontainers.postgres import PostgresContainer

# Import RBACService directly from file to avoid package side effects
spec = importlib.util.spec_from_file_location(
    "core.rbac", "yosai_intel_dashboard/src/core/rbac.py"
)
rbac = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(rbac)
RBACService = rbac.RBACService


class FailingRedis:
    async def get(self, key):  # pragma: no cover - simple failover stub
        raise ConnectionError("redis unavailable")

    async def setex(self, key, ttl, value):  # pragma: no cover - simple failover stub
        raise ConnectionError("redis unavailable")


@pytest.mark.integration
def test_rbac_fails_over_to_database():
    if not shutil.which("docker"):
        pytest.skip("docker not available")

    async def run_test():
        with PostgresContainer("postgres:15-alpine") as pg:
            dsn = pg.get_connection_url()
            pool = await asyncpg.create_pool(dsn=dsn)
            async with pool.acquire() as conn:
                await conn.execute(
                    "CREATE TABLE user_roles (user_id text, role text)"
                )
                await conn.execute(
                    "INSERT INTO user_roles (user_id, role) VALUES ($1, $2)",
                    "u1",
                    "admin",
                )

            service = RBACService(pool, FailingRedis())
            roles = await service.get_roles("u1")
            assert roles == ["admin"]
            await pool.close()

    asyncio.run(run_test())
