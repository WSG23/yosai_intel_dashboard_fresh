from __future__ import annotations

import pytest

from yosai_intel_dashboard.src.infrastructure.monitoring.alerts import (
    AlertManager,
    AlertThresholds,
)


class DummyNotificationService:
    def __init__(self) -> None:
        self.messages = []

    def send(self, message: str) -> None:  # pragma: no cover - simple recorder
        self.messages.append(message)


@pytest.mark.integration
def test_alert_manager_sends_notifications(monkeypatch):
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.infrastructure.monitoring.alerts.NotificationService",
        DummyNotificationService,
    )

    thresholds = AlertThresholds(
        metrics={"accuracy": 0.9},
        drift=0.1,
        error_spike=5,
    )
    manager = AlertManager(thresholds=thresholds)

    metrics_triggered = manager.check_metrics({"accuracy": 0.8})
    drift_triggered = manager.check_drift(0.2)
    error_triggered = manager.check_error_spike(10)

    assert metrics_triggered is True
    assert drift_triggered is True
    assert error_triggered is True

    messages = manager.notifier.messages
    assert len(messages) == 3
    assert any("Metric accuracy" in msg for msg in messages)
    assert any("Drift score" in msg for msg in messages)
    assert any("Error spike" in msg for msg in messages)
