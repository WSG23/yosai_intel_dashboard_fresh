from __future__ import annotations

from src.websocket.metrics_provider import MetricsProvider
from shared.events.names import EventName
from yosai_intel_dashboard.src.core.registry import ServiceRegistry


class DummyRepo:
    def __init__(self, data):
        self._data = data

    def snapshot(self):
        return self._data


class DummyBus:
    def __init__(self) -> None:
        self.events = []

    def publish(self, event_type: str, data, source=None) -> None:
        self.events.append((event_type, data))


def test_metrics_provider_injected_repo() -> None:
    repo = DummyRepo({"throughput": 1})
    bus = DummyBus()
    provider = MetricsProvider(bus, repo=repo, interval=0.01)
    import time
    time.sleep(0.02)
    provider.stop()
    assert (EventName.METRICS_UPDATE, repo.snapshot()) in bus.events


def test_metrics_provider_registry_lookup() -> None:
    repo = DummyRepo({"throughput": 2})
    ServiceRegistry.register("metrics_repository", repo)
    try:
        bus = DummyBus()
        provider = MetricsProvider(bus, interval=0.01)
        import time
        time.sleep(0.02)
        provider.stop()
        assert (EventName.METRICS_UPDATE, repo.snapshot()) in bus.events
    finally:
        ServiceRegistry.remove("metrics_repository")
