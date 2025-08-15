import asyncio
from yosai_intel_dashboard.src.services.analytics import queries


class FakePool:
    def __init__(self):
        self.query = None
        self.args = None

    async def fetch(self, query, *args):
        self.query = query
        self.args = args
        return []


def test_hourly_event_counts_uses_make_interval():
    pool = FakePool()
    asyncio.run(queries.hourly_event_counts(pool, 3))
    assert "make_interval" in pool.query
    assert "$1" in pool.query
    assert pool.args == (3,)


def test_hourly_event_counts_rejects_injection():
    pool = FakePool()
    malicious = "1; DROP TABLE access_events;--"
    asyncio.run(queries.hourly_event_counts(pool, malicious))  # type: ignore[arg-type]
    assert malicious not in pool.query
    assert pool.args == (malicious,)


def test_top_doors_uses_make_interval_and_limit():
    pool = FakePool()
    asyncio.run(queries.top_doors(pool, 7, limit=10))
    assert "make_interval" in pool.query
    assert "$1" in pool.query and "$2" in pool.query
    assert pool.args == (7, 10)


def test_top_doors_rejects_injection():
    pool = FakePool()
    malicious = "1; DROP TABLE access_events;--"
    asyncio.run(queries.top_doors(pool, malicious, limit=5))  # type: ignore[arg-type]
    assert malicious not in pool.query
    assert pool.args == (malicious, 5)

