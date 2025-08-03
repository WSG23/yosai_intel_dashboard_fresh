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
    start_conn = metrics.websocket_connections_total._value.get()
    start_reconnect = metrics.websocket_reconnect_attempts_total._value.get()
    start_ping = metrics.websocket_ping_failures_total._value.get()

    metrics.record_connection()
    metrics.record_reconnect_attempt()
    metrics.record_ping_failure()

    assert bus.events[0][0] == "metrics_update"
    assert bus.events[0][1]["websocket_connections_total"] == start_conn + 1
    assert bus.events[1][1]["websocket_reconnect_attempts_total"] == start_reconnect + 1
    assert bus.events[2][1]["websocket_ping_failures_total"] == start_ping + 1
