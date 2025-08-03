import time

from yosai_intel_dashboard.src.database.retry_strategy import RetryStrategy
from yosai_intel_dashboard.src.database._pooled_connection import _PooledConnection


class DummyConn:
    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    def work(self) -> str:
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("boom")
        return "ok"

    # Pool compatibility
    def health_check(self) -> bool:
        return True

    def close(self) -> None:
        pass


class DummyPool:
    def __init__(self, conn: DummyConn) -> None:
        self.conn = conn

    def get_connection(self) -> DummyConn:
        return self.conn

    def release_connection(self, conn: DummyConn) -> None:
        pass


def test_defaults_used(monkeypatch):
    """Without overrides, strategy defaults drive retries."""
    conn = DummyConn(failures=2)
    pool = DummyPool(conn)
    strategy = RetryStrategy(attempts=3, backoff=1)
    pc = _PooledConnection(pool, strategy)

    sleeps: list[float] = []
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.database.retry_strategy.time.sleep",
        lambda s: sleeps.append(s),
    )

    assert pc.call(lambda c: c.work()) == "ok"
    assert conn.calls == 3
    assert sleeps == [1, 2]


def test_overrides(monkeypatch):
    """Overrides for attempts and backoff are honoured."""
    conn = DummyConn(failures=4)
    pool = DummyPool(conn)
    # defaults would fail; overrides ensure success
    strategy = RetryStrategy(attempts=2, backoff=1)
    pc = _PooledConnection(pool, strategy)

    sleeps: list[float] = []
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.database.retry_strategy.time.sleep",
        lambda s: sleeps.append(s),
    )

    assert pc.call(lambda c: c.work(), attempts=5, backoff=2) == "ok"
    assert conn.calls == 5
    assert sleeps == [2, 4, 8, 16]
