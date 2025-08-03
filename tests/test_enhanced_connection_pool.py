import threading
import time
import importlib.util
from pathlib import Path
import sys

import threading
import time
import importlib.util
import types
from pathlib import Path
import sys

import pytest

spec_exc = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.infrastructure.config.database_exceptions",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "infrastructure"
    / "config"
    / "database_exceptions.py",

)
exc_module = importlib.util.module_from_spec(spec_exc)
sys.modules[spec_exc.name] = exc_module
spec_exc.loader.exec_module(exc_module)  # type: ignore
ConnectionValidationFailed = exc_module.ConnectionValidationFailed

metrics_pkg = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.connection_pool"
)
metrics_pkg.db_pool_active_connections = types.SimpleNamespace(set=lambda v: None)
metrics_pkg.db_pool_current_size = types.SimpleNamespace(set=lambda v: None)
metrics_pkg.db_pool_wait_seconds = types.SimpleNamespace(observe=lambda v: None)
sys.modules[
    "yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.connection_pool"
] = metrics_pkg

spec_ip = importlib.util.spec_from_file_location(
    "intelligent_connection_pool",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "database"
    / "intelligent_connection_pool.py",
)
ip_module = importlib.util.module_from_spec(spec_ip)
spec_ip.loader.exec_module(ip_module)  # type: ignore
CircuitBreaker = ip_module.CircuitBreaker
IntelligentConnectionPool = ip_module.IntelligentConnectionPool


class MockConnection:
    def __init__(self):
        self._connected = True

    def execute_query(self, query, params=None):
        return []

    def execute_command(self, command, params=None):
        return None

    def health_check(self):
        return self._connected

    def close(self):
        self._connected = False


class MockConnection:
    def __init__(self):
        self._connected = True

    def health_check(self):
        return self._connected

    def close(self):
        self._connected = False


def factory():
    return MockConnection()


def test_pool_metrics():
    pool = IntelligentConnectionPool(factory, 1, 2, timeout=1, shrink_timeout=1)
    conn = pool.get_connection()
    pool.release_connection(conn)
    metrics = pool.get_metrics()
    assert metrics["acquired"] == 1
    assert metrics["released"] == 1
    assert metrics["active"] <= 2


class BadConn:
    def health_check(self):
        return False

    def close(self):
        pass


def bad_factory():
    return BadConn()


def test_circuit_breaker_opens_on_failures():
    with pytest.raises(ConnectionValidationFailed):
        IntelligentConnectionPool(
            bad_factory,
            1,
            1,
            timeout=0.1,
            shrink_timeout=0,
            failure_threshold=2,
            recovery_timeout=1,
        )


def test_connection_count_under_load():
    pool = IntelligentConnectionPool(factory, 2, 4, timeout=1, shrink_timeout=1)
    results = []
    lock = threading.Lock()

    def worker():
        conn = pool.get_connection()
        with lock:
            results.append(conn)
        time.sleep(0.01)
        pool.release_connection(conn)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(set(results)) <= pool._max_pool_size
    metrics = pool.get_metrics()
    assert metrics["acquired"] == 20
    assert metrics["released"] == 20
