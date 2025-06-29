import pytest
import time
from config.connection_retry import ConnectionRetryManager, RetryConfig
from config.database_exceptions import ConnectionRetryExhausted


def test_retry_success(monkeypatch):
    attempts = []

    def func():
        attempts.append(1)
        return "ok"

    retry = ConnectionRetryManager(RetryConfig(max_attempts=3, base_delay=0))
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

    retry = ConnectionRetryManager(RetryConfig(max_attempts=5, base_delay=0))
    result = retry.run_with_retry(func)
    assert result == "done"
    assert len(calls) == 3


def test_retry_exhausted(monkeypatch):
    def func():
        raise RuntimeError("fail")

    retry = ConnectionRetryManager(RetryConfig(max_attempts=2, base_delay=0))
    with pytest.raises(ConnectionRetryExhausted):
        retry.run_with_retry(func)

