import asyncio
import importlib.util
import pathlib
import sys
import types

import asyncio
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SERVICES_PATH = ROOT / "yosai_intel_dashboard" / "src" / "services"

# Stub out heavy optional dependencies
dash_stub = types.ModuleType("dash")
dash_stub.Dash = object
sys.modules.setdefault("dash", dash_stub)
deps_stub = types.ModuleType("dash.dependencies")
deps_stub.Input = deps_stub.Output = deps_stub.State = object
sys.modules.setdefault("dash.dependencies", deps_stub)
services_pkg = types.ModuleType("services")
services_pkg.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_pkg)

spec = importlib.util.spec_from_file_location(
    "services.migration.framework",
    SERVICES_PATH / "migration" / "framework.py",
)
framework = importlib.util.module_from_spec(spec)
spec.loader.exec_module(framework)


class DummyPool:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.inserted = []
        self._fetch_count = 0
        self.executed_queries = []

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
        self.executed_queries.append(query)
        if query.startswith("TRUNCATE"):
            self.inserted.clear()


class SimpleMigration(framework.MigrationStrategy):
    async def run(self, source_pool):
        assert self.target_pool is not None
        while True:
            rows = await source_pool.fetch("SELECT")
            if not rows:
                break
            await self.target_pool.executemany("INSERT", rows)
            yield len(rows)


def test_migration_manager_progress():
    async def _run():
        src_pool = DummyPool(rows=[{"id": 1}])
        gw_pool = DummyPool()
        ev_pool = DummyPool()
        an_pool = DummyPool()

        pools = iter([src_pool, gw_pool, ev_pool, an_pool])

        async def fake_create_pool(*_, **__):
            return next(pools)

        strategies = [
            SimpleMigration("gateway_logs", "postgresql://gw", pool_factory=fake_create_pool),
            SimpleMigration("access_events", "postgresql://ev", pool_factory=fake_create_pool),
            SimpleMigration(
                "analytics_results", "postgresql://an", pool_factory=fake_create_pool
            ),
        ]

        mgr = framework.MigrationManager(
            "postgresql://source", strategies, pool_factory=fake_create_pool
        )
        await mgr.migrate()
        status = await mgr.status()
        assert status["progress"]["gateway_logs"] == 1

    asyncio.run(_run())


def test_rollback_table_whitelist():
    class DummyMigration(framework.MigrationStrategy):
        async def run(self, source_pool):
            yield 0

    async def _run():
        pool = DummyPool()
        strat = DummyMigration("gateway_logs", "postgresql://target")
        strat.target_pool = pool
        await strat.rollback()
        assert pool.executed_queries == ['TRUNCATE TABLE "gateway_logs" CASCADE']

        bad_pool = DummyPool()
        bad_strat = DummyMigration("bad_table", "postgresql://target")
        bad_strat.target_pool = bad_pool
        with pytest.raises(ValueError):
            await bad_strat.rollback()
        assert bad_pool.executed_queries == []

    asyncio.run(_run())
