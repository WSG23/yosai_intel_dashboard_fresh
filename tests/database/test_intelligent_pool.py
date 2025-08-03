import importlib.util
import importlib.util
import types
from pathlib import Path
import sys

exc_spec = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.infrastructure.config.database_exceptions",
    Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard/src/infrastructure/config/database_exceptions.py",
)
db_exc = importlib.util.module_from_spec(exc_spec)
exc_spec.loader.exec_module(db_exc)
sys.modules["yosai_intel_dashboard.src.infrastructure.config.database_exceptions"] = db_exc
config_pkg = types.ModuleType("yosai_intel_dashboard.src.infrastructure.config")
config_pkg.__path__ = []
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure", types.ModuleType("yosai_intel_dashboard.src.infrastructure")
)
sys.modules["yosai_intel_dashboard.src.infrastructure.config"] = config_pkg

metrics_pkg = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.connection_pool"
)
metrics_pkg.db_pool_active_connections = types.SimpleNamespace(set=lambda v: None)
metrics_pkg.db_pool_current_size = types.SimpleNamespace(set=lambda v: None)
metrics_pkg.db_pool_wait_seconds = types.SimpleNamespace(observe=lambda v: None)
sys.modules[
    "yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.connection_pool"
] = metrics_pkg

from yosai_intel_dashboard.src.database.intelligent_connection_pool import IntelligentConnectionPool


class MockConnection:
    def __init__(self):
        self._connected = True

    def health_check(self):
        return self._connected

    def close(self):
        self._connected = False


def factory():
    return MockConnection()


def test_pool_resizes_and_reports_metrics():
    pool = IntelligentConnectionPool(
        factory, min_size=1, max_size=3, timeout=1, shrink_timeout=0
    )

    c1 = pool.get_connection()
    c2 = pool.get_connection()

    # After requesting a second connection utilization should trigger expansion
    assert pool._max_size >= 2

    pool.release_connection(c1)
    pool.release_connection(c2)

    # Shrink happens immediately because shrink_timeout=0
    assert pool._max_size == 1

    metrics = pool.get_metrics()
    assert metrics["acquired"] == 2
    assert metrics["released"] == 2
    assert "avg_acquire_time" in metrics


def test_warmup_prefills_pool():
    class WarmConn:
        def __init__(self):
            self.warm_calls = 0
            self._connected = True

        def execute_query(self, query, params=None):
            self.warm_calls += 1
            return []

        def execute_command(self, command, params=None):
            return None

        def health_check(self):
            return self._connected

        def close(self):
            self._connected = False

    def warm_factory():
        return WarmConn()

    pool = IntelligentConnectionPool(warm_factory, 1, 2, timeout=1, shrink_timeout=1)
    conn, _ = pool._pool[0]
    assert conn.warm_calls == 1

    conn.close()
    pool._pool.clear()
    pool._active = 0

    pool.warmup()
    assert pool._active == 1
    conn, _ = pool._pool[0]
    assert conn.warm_calls == 1
