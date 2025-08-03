import importlib.util
import sys
import types
from pathlib import Path


def test_clients_use_distinct_dbs(monkeypatch):
    monkeypatch.setenv("SESSION_REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("METRICS_REDIS_URL", "redis://localhost:6379/1")

    class DummyRedis:
        def __init__(self, db: int) -> None:
            self.connection_pool = types.SimpleNamespace(connection_kwargs={"db": db})

        @classmethod
        def from_url(cls, url: str) -> "DummyRedis":
            db = int(url.rsplit("/", 1)[-1])
            return cls(db)

    monkeypatch.setitem(sys.modules, "redis", types.SimpleNamespace(Redis=DummyRedis))
    path = (
        Path(__file__).resolve().parents[2]
        / "yosai_intel_dashboard/src/infrastructure/cache/redis_client.py"
    )
    spec = importlib.util.spec_from_file_location("redis_client", path)
    assert spec and spec.loader
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)  # type: ignore[union-attr]
    session = rc.get_session_client()
    metrics = rc.get_metrics_client()
    assert session.connection_pool.connection_kwargs["db"] == 0
    assert metrics.connection_pool.connection_kwargs["db"] == 1
    assert rc.redis_client is session
