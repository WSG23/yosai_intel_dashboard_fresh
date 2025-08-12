from __future__ import annotations

from src.websocket import metrics


class DummyBus:
    def __init__(self) -> None:
        self.events = []

    def publish(
        self, event_type: str, data, source=None
    ) -> None:  # pragma: no cover - simple bus
        self.events.append((event_type, data))

def test_websocket_metrics_publish_updates():
    bus = DummyBus()
    metrics.set_event_bus(bus)
    metrics.record_connection()
    metrics.record_reconnect_attempt()
    metrics.record_ping_failure()
    assert bus.events[0][0] == "metrics_update"
    assert "websocket_connections_total" in bus.events[0][1]
    assert "websocket_reconnect_attempts_total" in bus.events[0][1]
    assert "websocket_ping_failures_total" in bus.events[0][1]
    assert len(bus.events) == 3

