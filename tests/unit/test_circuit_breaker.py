import time

import importlib.util
import sys
import types
from pathlib import Path

import pytest


def _load_module(name: str, relative_path: str):
    path = Path(__file__).resolve().parents[1] / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


config_pkg = types.ModuleType("config")
config_pkg.__path__ = []  # type: ignore[attr-defined]
sys.modules["config"] = config_pkg

exc_mod = _load_module(
    "config.database_exceptions",
    "yosai_intel_dashboard/src/infrastructure/config/database_exceptions.py",
)
ConnectionRetryExhausted = exc_mod.ConnectionRetryExhausted

protocols_mod = _load_module(
    "config.protocols",
    "yosai_intel_dashboard/src/infrastructure/config/protocols.py",
)
_ = protocols_mod

circuit_mod = _load_module(
    "config.circuit_breaker",
    "yosai_intel_dashboard/src/infrastructure/config/circuit_breaker.py",
)
CircuitBreaker = circuit_mod.CircuitBreaker
CircuitBreakerOpen = circuit_mod.CircuitBreakerOpen

conn_mod = _load_module(
    "config.connection_retry",
    "yosai_intel_dashboard/src/infrastructure/config/connection_retry.py",
)
ConnectionRetryManager = conn_mod.ConnectionRetryManager
RetryConfig = conn_mod.RetryConfig


def test_circuit_breaker_uses_fallback():
    calls = []

    def failing():
        calls.append(1)
        raise RuntimeError("boom")

    fallback_calls = []

    def fallback():
        fallback_calls.append(1)
        return "fallback"

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1, fallback=fallback)
    manager = ConnectionRetryManager(
        RetryConfig(max_attempts=1, base_delay=0, jitter=False),
        circuit_breaker=breaker,
    )

    with pytest.raises(ConnectionRetryExhausted):
        manager.run_with_retry(failing)
    assert breaker.state == "open"
    result = manager.run_with_retry(lambda: "ok")
    assert result == "fallback"
    assert len(calls) == 1
    assert len(fallback_calls) == 1


def test_circuit_breaker_recovery():
    def failing():
        raise RuntimeError("boom")

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
    manager = ConnectionRetryManager(
        RetryConfig(max_attempts=1, base_delay=0, jitter=False),
        circuit_breaker=breaker,
    )

    with pytest.raises(ConnectionRetryExhausted):
        manager.run_with_retry(failing)
    with pytest.raises(CircuitBreakerOpen):
        manager.run_with_retry(lambda: "should fail")
    time.sleep(0.05)
    result = manager.run_with_retry(lambda: "ok")
    assert result == "ok"
    assert breaker.state == "closed"
