from __future__ import annotations

"""Prometheus metrics and EventBus integration for WebSocket activity."""

from prometheus_client import REGISTRY, Counter, start_http_server
from prometheus_client.core import CollectorRegistry

from typing import Any, Dict, Protocol


class EventBusProtocol(Protocol):
    def publish(self, event_type: str, data: Dict[str, Any], source: str | None = None) -> None: ...

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

_event_bus: EventBusProtocol | None = None

_metrics_started = False

def set_event_bus(bus: EventBusProtocol) -> None:
    """Configure the ``EventBus`` used for publishing metric updates."""
    global _event_bus
    _event_bus = bus

def _publish(name: str, value: float) -> None:
    if _event_bus:
        try:
            _event_bus.publish("metrics_update", {name: value})
        except Exception:  # pragma: no cover - best effort
            pass


def start_metrics_server(port: int = 8003) -> None:
    """Expose metrics on the given port if not already started."""
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True

def record_connection() -> None:
    """Increment connection counter and publish update."""
    websocket_connections_total.inc()
    _publish(
        "websocket_connections_total", websocket_connections_total._value.get()  # type: ignore[attr-defined]
    )

def record_reconnect_attempt() -> None:
    """Increment reconnect counter and publish update."""
    websocket_reconnect_attempts_total.inc()
    _publish(
        "websocket_reconnect_attempts_total",
        websocket_reconnect_attempts_total._value.get(),  # type: ignore[attr-defined]
    )

def record_ping_failure() -> None:
    """Increment ping failure counter and publish update."""
    websocket_ping_failures_total.inc()
    _publish(
        "websocket_ping_failures_total",
        websocket_ping_failures_total._value.get(),  # type: ignore[attr-defined]
    )

__all__ = [
    "websocket_connections_total",
    "websocket_reconnect_attempts_total",
    "websocket_ping_failures_total",
    "record_connection",
    "record_reconnect_attempt",
    "record_ping_failure",
    "set_event_bus",
    "start_metrics_server",
]
