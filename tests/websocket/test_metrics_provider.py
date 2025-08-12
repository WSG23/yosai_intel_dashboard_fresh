from src.repository import InMemoryMetricsRepository
from src.websocket.metrics_provider import MetricsProvider
from src.common.config import ConfigService
from shared.events.names import EventName

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
    assert (EventName.METRICS_UPDATE, repo.snapshot()) in bus.events
