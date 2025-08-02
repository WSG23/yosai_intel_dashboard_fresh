import pytest

from yosai_intel_dashboard.src.services.analytics import timescale_queries as tq


def test_build_queries():
    q1 = tq.build_time_bucket_query("1 hour", table="t")
    assert "1 hour" in str(q1)
    q2 = tq.build_sliding_window_query(3600, 60, table="t")
    assert "COUNT(*)" in str(q2)


@pytest.mark.asyncio
async def test_fetch_time_buckets(monkeypatch):
    class DummyPool:
        def __init__(self):
            self.calls = []

        async def fetch(self, query, start, end):
            self.calls.append(query)
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
