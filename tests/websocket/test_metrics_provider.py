from __future__ import annotations

from src.websocket.metrics_provider import MetricsProvider, generate_sample_metrics
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

    def publish(self, event_type: str, data, source=None) -> None:  # pragma: no cover - simple bus
        self.events.append((event_type, data))


def _wait_provider(provider) -> None:
    import time
    time.sleep(0.02)
    provider.stop()


def test_metrics_provider_injected_repo() -> None:
    repo = DummyRepo({"throughput": 1})
    bus = DummyBus()
    provider = MetricsProvider(bus, repo=repo, interval=0.01)
    _wait_provider(provider)
    assert bus.events == [(EventName.METRICS_UPDATE, repo.snapshot())]


def test_metrics_provider_registry_lookup() -> None:
    repo = DummyRepo({"throughput": 2})
    ServiceRegistry.register("metrics_repository", repo)
    try:
        bus = DummyBus()
        provider = MetricsProvider(bus, interval=0.01)
        _wait_provider(provider)
        assert bus.events == [(EventName.METRICS_UPDATE, repo.snapshot())]
    finally:
        ServiceRegistry.remove("metrics_repository")


def test_generate_sample_metrics_registry_lookup() -> None:
    repo = DummyRepo({"throughput": 3})
    ServiceRegistry.register("metrics_repository", repo)
    try:
        assert generate_sample_metrics() == repo.snapshot()
    finally:
        ServiceRegistry.remove("metrics_repository")
