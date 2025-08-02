import pytest

from yosai_intel_dashboard.src.infrastructure.monitoring.alerts import (
    AlertManager,
    AlertThresholds,
)


class DummyNotifier:
    def __init__(self):
        self.messages = []

    def send(self, message: str) -> None:  # pragma: no cover - simple
        self.messages.append(message)


def setup_alerts(monkeypatch, thresholds):
    dummy = DummyNotifier()
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.infrastructure.monitoring.alerts.NotificationService",
        lambda: dummy,
    )
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.infrastructure.monitoring.alerts._load_thresholds",
        lambda: AlertThresholds(**thresholds),
    )
    return dummy


def test_metric_alert_triggers_notification(monkeypatch):
    notifier = setup_alerts(
        monkeypatch,
        {"metrics": {"accuracy": 0.9}, "drift": 0.2, "error_spike": 5},
    )
    manager = AlertManager()
    triggered = manager.check_metrics({"accuracy": 0.8})
    assert triggered is True
    assert notifier.messages


def test_drift_and_error_alerts(monkeypatch):
    notifier = setup_alerts(
        monkeypatch,
        {"metrics": {}, "drift": 0.1, "error_spike": 3},
    )
    manager = AlertManager()
    drift_triggered = manager.check_drift(0.2)
    error_triggered = manager.check_error_spike(5)
    assert drift_triggered and error_triggered
    assert len(notifier.messages) == 2


def test_no_alert_when_within_threshold(monkeypatch):
    notifier = setup_alerts(
        monkeypatch,
        {"metrics": {"accuracy": 0.5}, "drift": 0.5, "error_spike": 10},
    )
    manager = AlertManager()
    assert manager.check_metrics({"accuracy": 0.9}) is False
    assert manager.check_drift(0.1) is False
    assert manager.check_error_spike(5) is False
    assert not notifier.messages
