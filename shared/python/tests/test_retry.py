import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))
from shared.python import retry as retry_mod


def test_custom_backoff_respected(monkeypatch):
    delays = []

    def fake_sleep(seconds: float) -> None:
        delays.append(seconds)

    # Remove jitter for deterministic behavior
    monkeypatch.setattr(retry_mod, "_ajitter", lambda base, jitter=0.2: base)
    monkeypatch.setattr(retry_mod, "_sleep", fake_sleep)

    attempts = {"count": 0}

    def flakey():

        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("boom")
        return "ok"

    assert retry_mod.retry(flakey, attempts=3, base_delay=1) == "ok"
    assert delays == [1, 2]


def test_retryerror_includes_last_exception(monkeypatch):
    monkeypatch.setattr(retry_mod, "_sleep", lambda s: None)
    monkeypatch.setattr(retry_mod, "_ajitter", lambda base, jitter=0.2: base)

    def always_fail():
        raise RuntimeError("kaput")

    with pytest.raises(retry_mod.RetryError) as excinfo:
        retry_mod.retry(always_fail, attempts=2, base_delay=0)

    assert "kaput" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, RuntimeError)
