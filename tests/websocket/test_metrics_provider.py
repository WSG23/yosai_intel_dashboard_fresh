import time

from src.websocket.metrics_provider import MetricsProvider


class DummyBus:
    def __init__(self) -> None:
        self._subs = {}

    def publish(self, event_type: str, data):
        for handler in self._subs.get(event_type, []):
            handler(data)

    def subscribe(self, event_type: str, handler):
        self._subs.setdefault(event_type, []).append(handler)


def test_metrics_provider_publishes_updates():
    bus = DummyBus()
    events = []
    bus.subscribe('metrics_update', lambda data: events.append(data))
    provider = MetricsProvider(bus, interval=0.01)
    time.sleep(0.05)
    provider.stop()
    assert events
    assert 'performance' in events[0]
