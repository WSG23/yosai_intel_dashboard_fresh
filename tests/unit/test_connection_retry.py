import time

import pytest

import importlib.util
import sys
import types
from pathlib import Path


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
_ = protocols_mod  # silence unused variable

circuit_mod = _load_module(
    "config.circuit_breaker",
    "yosai_intel_dashboard/src/infrastructure/config/circuit_breaker.py",
)
_ = circuit_mod

conn_mod = _load_module(
    "config.connection_retry",
    "yosai_intel_dashboard/src/infrastructure/config/connection_retry.py",
)
ConnectionRetryManager = conn_mod.ConnectionRetryManager
RetryConfig = conn_mod.RetryConfig


def test_retry_success(monkeypatch):
    attempts = []

    def func():
        attempts.append(1)
        return "ok"

    retry = ConnectionRetryManager(
        RetryConfig(max_attempts=3, base_delay=0, jitter=False)
    )
    result = retry.run_with_retry(func)
    assert result == "ok"
    assert len(attempts) == 1


def test_retry_attempts(monkeypatch):
    calls = []

    def func():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("boom")
        return "done"

    retry = ConnectionRetryManager(
        RetryConfig(max_attempts=5, base_delay=0, jitter=False)
    )
    result = retry.run_with_retry(func)
    assert result == "done"
    assert len(calls) == 3


def test_retry_exhausted(monkeypatch):
    def func():
        raise RuntimeError("fail")

    retry = ConnectionRetryManager(
        RetryConfig(max_attempts=2, base_delay=0, jitter=False)
    )
    with pytest.raises(ConnectionRetryExhausted):
        retry.run_with_retry(func)


def test_backoff_and_max_delay(monkeypatch):
    delays = []

    def fake_sleep(d):
        delays.append(d)

    monkeypatch.setattr(time, "sleep", fake_sleep)

    calls = []

    def func():
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("boom")
        return "ok"

    cfg = RetryConfig(
        max_attempts=3,
        base_delay=1,
        backoff_factor=3,
        max_delay=2,
        jitter=False,
    )
    result = ConnectionRetryManager(cfg).run_with_retry(func)
    assert result == "ok"
    assert delays == [1, 2]
