from src.repository import InMemoryMetricsRepository
from src.websocket.metrics_provider import MetricsProvider
from yosai_intel_dashboard.src.core.registry import ServiceRegistry


class DummyBus:
    def __init__(self) -> None:
        self.events = []

    def publish(self, event_type: str, data, source=None) -> None:
        self.events.append((event_type, data))


def test_metrics_provider_publishes_snapshot() -> None:
    repo = InMemoryMetricsRepository(performance={"throughput": 1})
    ServiceRegistry.register("metrics_repository", repo)
    bus = DummyBus()
    provider = MetricsProvider(bus, interval=0.01)
    import time
    time.sleep(0.02)
    provider.stop()
    ServiceRegistry.remove("metrics_repository")
    assert ("metrics_update", repo.snapshot()) in bus.events
