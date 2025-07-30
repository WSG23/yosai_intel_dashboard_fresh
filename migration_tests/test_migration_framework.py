import asyncio
import importlib.util
import pathlib
import sys
import types

import pytest

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[1] / "services"
services_pkg = types.ModuleType("services")
services_pkg.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_pkg)

spec = importlib.util.spec_from_file_location(
    "services.migration.framework",
    SERVICES_PATH / "migration" / "framework.py",
)
framework = importlib.util.module_from_spec(spec)
spec.loader.exec_module(framework)

spec = importlib.util.spec_from_file_location(
    "services.migration.strategies.gateway_migration",
    SERVICES_PATH / "migration" / "strategies" / "gateway_migration.py",
)
gateway_migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway_migration)

spec = importlib.util.spec_from_file_location(
    "services.migration.strategies.events_migration",
    SERVICES_PATH / "migration" / "strategies" / "events_migration.py",
)
events_migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(events_migration)

spec = importlib.util.spec_from_file_location(
    "services.migration.strategies.analytics_migration",
    SERVICES_PATH / "migration" / "strategies" / "analytics_migration.py",
)
analytics_migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analytics_migration)


class DummyPool:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.inserted = []
        self._fetch_count = 0

    async def fetch(self, *a, **k):
        self._fetch_count += 1
        if self._fetch_count > 1:
            return []
        return list(self.rows)

    async def fetchval(self, *a, **k):
        return len(self.inserted)

    async def executemany(self, _query, values):
        self.inserted.extend(list(values))

    def acquire(self):
        return self

    def release(self, _c=None):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def execute(self, query):
        if query.startswith("TRUNCATE"):
            self.inserted.clear()


@pytest.mark.asyncio
async def test_migration_manager_progress(monkeypatch):
    src_pool = DummyPool(rows=[{"id": 1}])
    gw_pool = DummyPool()
    ev_pool = DummyPool()
    an_pool = DummyPool()

    pools = iter([src_pool, gw_pool, ev_pool, an_pool])

    async def fake_create_pool(*_, **__):
        return next(pools)

    monkeypatch.setattr(framework.asyncpg, "create_pool", fake_create_pool)

    mgr = framework.MigrationManager(
        "postgresql://source",
        [
            gateway_migration.GatewayMigration("postgresql://gw"),
            events_migration.EventsMigration("postgresql://ev"),
            analytics_migration.AnalyticsMigration("postgresql://an"),
        ],
    )
    await mgr.migrate()
    status = await mgr.status()
    assert status["progress"]["gateway_logs"] == 1
