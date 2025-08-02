import logging
from typing import List

import pandas as pd
import pytest

from services import model_monitoring_service as mms


class DummyDispatcher:
    def __init__(self, fail: bool = False) -> None:
        self.messages: List[str] = []
        self.fail = fail

    def send_alert(self, message: str) -> None:
        if self.fail:
            raise RuntimeError("boom")
        self.messages.append(message)


def setup_env(monkeypatch) -> None:
    monkeypatch.setenv("KS_THRESHOLD", "0.5")
    monkeypatch.setenv("PSI_THRESHOLD", "0.5")
    monkeypatch.setenv("WASSERSTEIN_THRESHOLD", "0.5")


def test_alert_triggered(monkeypatch):
    setup_env(monkeypatch)

    monkeypatch.setattr(mms, "ks_2samp", lambda a, b: (0.6, None))
    monkeypatch.setattr(mms, "wasserstein_distance", lambda a, b: 0.7)
    monkeypatch.setattr(mms, "compute_psi", lambda base, cur: {"a": 0.8})

    dispatcher = DummyDispatcher()
    service = mms.ModelMonitoringService(dispatcher=dispatcher)

    df_base = pd.DataFrame({"a": [1, 1, 1]})
    df_cur = pd.DataFrame({"a": [2, 2, 2]})
    service.check_drift(df_base, df_cur)

    assert dispatcher.messages
    msg = dispatcher.messages[0]
    assert "KS" in msg and "PSI" in msg and "Wasserstein" in msg


def test_alert_errors_logged(monkeypatch, caplog):
    setup_env(monkeypatch)

    monkeypatch.setattr(mms, "ks_2samp", lambda a, b: (0.6, None))
    monkeypatch.setattr(mms, "wasserstein_distance", lambda a, b: 0.7)
    monkeypatch.setattr(mms, "compute_psi", lambda base, cur: {"a": 0.8})

    dispatcher = DummyDispatcher(fail=True)
    service = mms.ModelMonitoringService(dispatcher=dispatcher)

    df_base = pd.DataFrame({"a": [1, 1, 1]})
    df_cur = pd.DataFrame({"a": [2, 2, 2]})

    with caplog.at_level(logging.WARNING):
        service.check_drift(df_base, df_cur)

    assert "Alert dispatch failed" in caplog.text

