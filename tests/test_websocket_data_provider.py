import time

from core.events import EventBus
from yosai_intel_dashboard.src.services.websocket_data_provider import WebSocketDataProvider


def test_websocket_data_provider_publishes():
    bus = EventBus()
    events = []
    bus.subscribe("analytics_update", lambda d: events.append(d))
    provider = WebSocketDataProvider(bus, interval=0.01)
    time.sleep(0.05)
    provider.stop()
    assert events
