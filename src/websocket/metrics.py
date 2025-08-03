"""Prometheus metrics and EventBus integration for WebSocket activity."""
from __future__ import annotations

from typing import Dict

from prometheus_client import REGISTRY, Counter, start_http_server
from prometheus_client.core import CollectorRegistry

from src.common.events import EventBus, EventPublisher

# Avoid duplicate registration when the module is imported multiple times.
if "websocket_connections_total" not in REGISTRY._names_to_collectors:
    websocket_connections_total = Counter(
        "websocket_connections_total", "Total websocket connections"
    )
    websocket_reconnect_attempts_total = Counter(
        "websocket_reconnect_attempts_total",
        "Total websocket reconnect attempts",
    )
    websocket_ping_failures_total = Counter(
        "websocket_ping_failures_total", "Total websocket ping failures"
    )
else:  # pragma: no cover - defensive for test imports
    registry = CollectorRegistry()
    websocket_connections_total = Counter(
        "websocket_connections_total",
        "Total websocket connections",
        registry=registry,
    )
    websocket_reconnect_attempts_total = Counter(
        "websocket_reconnect_attempts_total",
        "Total websocket reconnect attempts",
        registry=registry,
    )
    websocket_ping_failures_total = Counter(
        "websocket_ping_failures_total",
        "Total websocket ping failures",
        registry=registry,
    )


class WebSocketMetrics(EventPublisher):
    """Publish metric snapshots on every counter update."""

    def __init__(self, event_bus: EventBus) -> None:
        super().__init__(event_bus)

    def snapshot(self) -> Dict[str, float]:
        return {
            "websocket_connections_total": websocket_connections_total._value.get(),  # type: ignore[attr-defined]
            "websocket_reconnect_attempts_total": websocket_reconnect_attempts_total._value.get(),  # type: ignore[attr-defined]
            "websocket_ping_failures_total": websocket_ping_failures_total._value.get(),  # type: ignore[attr-defined]
        }

    def _publish_snapshot(self) -> None:
        self.publish_event("metrics_update", self.snapshot())

    def record_connection(self) -> None:
        """Increment connection counter and publish update."""
        websocket_connections_total.inc()
        self._publish_snapshot()

    def record_reconnect_attempt(self) -> None:
        """Increment reconnect counter and publish update."""
        websocket_reconnect_attempts_total.inc()
        self._publish_snapshot()

    def record_ping_failure(self) -> None:
        """Increment ping failure counter and publish update."""
        websocket_ping_failures_total.inc()
        self._publish_snapshot()

    def publish_snapshot(self) -> None:
        """Explicitly publish the current metric snapshot."""
        self._publish_snapshot()


_metrics_started = False


def start_metrics_server(port: int = 8003) -> None:
    """Expose metrics on the given port if not already started."""
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True


__all__ = [
    "websocket_connections_total",
    "websocket_reconnect_attempts_total",
    "websocket_ping_failures_total",
    "WebSocketMetrics",
    "start_metrics_server",
]
