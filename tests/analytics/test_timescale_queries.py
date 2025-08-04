from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest
import sqlalchemy.sql as sql
from sqlalchemy.sql.elements import TextClause

sql.TextClause = TextClause  # ensure attribute for import

# setup paths
ROOT = pathlib.Path(__file__).resolve().parents[2] / "yosai_intel_dashboard/src"
sys.path.append(str(ROOT))

# Load SecureQueryBuilder without importing the full infrastructure package
import types

infrastructure_pkg = types.ModuleType("infrastructure")
infrastructure_pkg.__path__ = [str(ROOT / "infrastructure")]
security_pkg = types.ModuleType("infrastructure.security")
security_pkg.__path__ = [str(ROOT / "infrastructure/security")]
sys.modules.setdefault("infrastructure", infrastructure_pkg)
sys.modules.setdefault("infrastructure.security", security_pkg)

spec_sq = importlib.util.spec_from_file_location(
    "infrastructure.security.query_builder",
    ROOT / "infrastructure/security/query_builder.py",
)
secure_module = importlib.util.module_from_spec(spec_sq)
sys.modules.setdefault("infrastructure.security.query_builder", secure_module)
assert spec_sq.loader is not None
spec_sq.loader.exec_module(secure_module)

spec = importlib.util.spec_from_file_location(
    "tq",
    ROOT / "services/analytics/timescale_queries.py",
)
tq = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(tq)


def test_build_queries():
    q1 = tq.build_time_bucket_query("1 hour", table="t")
    assert "time_bucket($3" in str(q1)
    q2 = tq.build_sliding_window_query(3600, 60, table="t")
    assert "$3" in str(q2)


@pytest.mark.asyncio
async def test_fetch_time_buckets(monkeypatch):
    class DummyPool:
        def __init__(self):
            self.calls = []

        async def fetch(self, query, *params):
            self.calls.append((query, params))
            return [dict(bucket=1, value=2)]

    pool = DummyPool()
    res = await tq.fetch_time_buckets(pool, 1, 2)
    assert res == [{"bucket": 1, "value": 2}]
    assert pool.calls


@pytest.mark.asyncio
async def test_fetch_sliding_window_error(monkeypatch):
    class DummyPool:
        async def fetch(self, *a):
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await tq.fetch_sliding_window(DummyPool(), 1, 2)


@pytest.mark.asyncio
async def test_malicious_inputs_are_parameterized():
    class DummyPool:
        def __init__(self):
            self.last = None

        async def fetch(self, query, *params):
            self.last = (query, params)
            return []

    pool = DummyPool()
    interval = "1 hour; DROP TABLE"  # malicious interval
    filters = {"name": "bob'; DROP TABLE users; --"}
    await tq.fetch_time_buckets(pool, 1, 2, bucket_size=interval, extra_filters=filters)
    assert interval not in pool.last[0]
    assert filters["name"] not in pool.last[0]
    assert filters["name"] in pool.last[1]


@pytest.mark.asyncio
async def test_malicious_filter_column_rejected():
    class DummyPool:
        async def fetch(self, *a):
            return []

    with pytest.raises(ValueError):
        await tq.fetch_time_buckets(DummyPool(), 1, 2, extra_filters={"bad;DROP": "x"})
