import threading
import time

import threading
import time
import importlib.util
import types
from pathlib import Path
import sys

import pytest

# Provide lightweight database_exceptions without triggering heavy config imports
exc_spec = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.infrastructure.config.database_exceptions",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard/src/infrastructure/config/database_exceptions.py",
)
db_exc = importlib.util.module_from_spec(exc_spec)
exc_spec.loader.exec_module(db_exc)
sys.modules["yosai_intel_dashboard.src.infrastructure.config.database_exceptions"] = db_exc

# Stub the parent package to bypass its __init__
config_pkg = types.ModuleType("yosai_intel_dashboard.src.infrastructure.config")
config_pkg.__path__ = []  # mark as package
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure", types.ModuleType("yosai_intel_dashboard.src.infrastructure")
)
sys.modules["yosai_intel_dashboard.src.infrastructure.config"] = config_pkg
ConnectionValidationFailed = db_exc.ConnectionValidationFailed

from yosai_intel_dashboard.src.database.intelligent_connection_pool import (
    CircuitBreaker,
    IntelligentConnectionPool,
)


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
    pool = IntelligentConnectionPool(
        bad_factory,
        1,
        1,
        timeout=0.1,
        shrink_timeout=0,
        failure_threshold=2,
        recovery_timeout=1,
    )
    with pytest.raises(ConnectionValidationFailed):
        pool.get_connection()
    # second attempt should immediately fail due to open circuit
    with pytest.raises(ConnectionValidationFailed):
        pool.get_connection()


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
