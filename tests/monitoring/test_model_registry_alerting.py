from __future__ import annotations

from types import SimpleNamespace

from yosai_intel_dashboard.src.infrastructure.monitoring.model_registry_alerting import (
    ModelRegistryAlerting,
)


class DummyAlertManager:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def notify(self, message: str) -> None:  # pragma: no cover - simple recorder
        self.messages.append(message)


class DummyRegistry:
    def __init__(self) -> None:
        self.metric_thresholds = {"accuracy": 0.9}
        self.drift_thresholds = {"feature": 0.1}

    def list_models(self):  # pragma: no cover - simple stub
        return [SimpleNamespace(name="model", is_active=True, metrics={"accuracy": 0.8})]

    def get_drift_metrics(self, name: str):  # pragma: no cover - simple stub
        return {"feature": 0.2}


def test_registry_alerting_triggers_notifications():
    manager = DummyAlertManager()
    registry = DummyRegistry()
    alerting = ModelRegistryAlerting(registry, alert_manager=manager)

    alerting.check()

    assert any("accuracy" in msg for msg in manager.messages)
    assert any("drift" in msg for msg in manager.messages)


def test_no_alert_when_within_threshold():
    class CleanRegistry(DummyRegistry):
        def list_models(self):  # pragma: no cover - simple stub
            return [SimpleNamespace(name="model", is_active=True, metrics={"accuracy": 0.95})]

        def get_drift_metrics(self, name: str):  # pragma: no cover - simple stub
            return {"feature": 0.05}

    manager = DummyAlertManager()
    registry = CleanRegistry()
    alerting = ModelRegistryAlerting(registry, alert_manager=manager)

    alerting.check()

    assert not manager.messages
