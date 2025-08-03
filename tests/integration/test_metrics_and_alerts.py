from __future__ import annotations

import importlib
import sys
import types

import pytest


@pytest.mark.integration
def test_metrics_update_triggers_alerts(monkeypatch):
    """Prometheus gauges update and alerts fire on threshold breach."""

    class DummyEventBus:
        def emit(self, event, payload):
            pass

        def subscribe(self, *a, **k):
            pass

    class DummyService:
        async def log_evaluation(self, *args, **kwargs):
            pass

    class DummyPublisher:
        def __init__(self, event_bus=None):
            pass

        def publish(self, payload):
            pass

    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.core.events",
        types.SimpleNamespace(EventBus=DummyEventBus),
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.model_monitoring_service",
        types.SimpleNamespace(ModelMonitoringService=DummyService),
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.publishing_service",
        types.SimpleNamespace(PublishingService=DummyPublisher),
    )

    mm = importlib.import_module(
        "yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.model_metrics"
    )

    class DummyNotificationService:
        def __init__(self) -> None:
            self.messages: list[str] = []

        def send(self, message: str) -> None:  # pragma: no cover - simple recorder
            self.messages.append(message)

    import yosai_intel_dashboard.src.infrastructure.monitoring.alerts as alerts

    monkeypatch.setattr(
        alerts,
        "NotificationService",
        DummyNotificationService,
    )

    thresholds = alerts.AlertThresholds(metrics={"accuracy": 0.9}, drift=0.1)
    manager = alerts.AlertManager(thresholds=thresholds)

    class Metrics:
        accuracy = 0.8
        precision = 0.85
        recall = 0.9
        drift = 0.2

    mm.update_model_metrics(Metrics())

    metrics_triggered = manager.check_metrics({"accuracy": Metrics.accuracy})
    drift_triggered = manager.check_drift(Metrics.drift)

    assert metrics_triggered is True
    assert drift_triggered is True
    assert mm.model_accuracy._value.get() == Metrics.accuracy
    assert mm.model_drift._value.get() == Metrics.drift
    assert manager.notifier.messages == [
        "Metric accuracy below threshold: 0.8 < 0.9",
        "Drift score 0.2 exceeds threshold 0.1",
    ]

