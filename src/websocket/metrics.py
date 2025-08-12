"""Prometheus metrics helpers for WebSocket activity.

The real project exposes websocket connection metrics via Prometheus and also
publishes updates on an application event bus.  The exercises in this kata only
need a very small subset of that behaviour, therefore this module provides a
minimal façade around a couple of :mod:`prometheus_client` counters.  A caller
can register an arbitrary event bus via :func:`set_event_bus`; whenever one of
the ``record_*`` helpers is invoked the counters are incremented and the current
snapshot is published on that bus.

The tests use a very small stand‑in bus exposing ``publish`` consistent with the
``EventBus`` interface.
"""

from __future__ import annotations

from typing import Dict

from shared.events.bus import EventBus
from shared.events.names import EventName

try:
    from prometheus_client import REGISTRY, Counter, start_http_server
    from prometheus_client.core import CollectorRegistry
except Exception:  # pragma: no cover - optional dependency
    class _DummyRegistry:
        _names_to_collectors: Dict[str, object] = {}

    REGISTRY = _DummyRegistry()

    def start_http_server(*_, **__):  # type: ignore[no-redef]
        return None

    class Counter:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            self._count = 0.0

            class _V:
                def __init__(self, outer: "Counter") -> None:
                    self._outer = outer

                def get(self) -> float:
                    return self._outer._count

            self._value = _V(self)

        def inc(self, amount: float = 1.0, *args, **kwargs) -> None:
            self._count += amount

_event_bus: EventBus | None = None
_metrics_started = False

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

def _counter_value(counter: Counter) -> float:
    try:
        return counter._value.get()  # type: ignore[attr-defined]
    except AttributeError:
        return 0.0


def _snapshot() -> Dict[str, float]:
    """Return the current metric values."""
    return {
        "websocket_connections_total": _counter_value(websocket_connections_total),
        "websocket_reconnect_attempts_total": _counter_value(
            websocket_reconnect_attempts_total
        ),
        "websocket_ping_failures_total": _counter_value(
            websocket_ping_failures_total
        ),
    }


def _publish_snapshot() -> None:
    """Publish the metric snapshot on the configured event bus, if any."""
    if _event_bus is None:
        return
    payload = _snapshot()
    _event_bus.publish(EventName.METRICS_UPDATE, payload)


def set_event_bus(bus: EventBus) -> None:
    """Configure the event bus used for publishing updates."""
    global _event_bus
    _event_bus = bus


def record_connection() -> None:
    """Increment connection counter and publish an update."""
    websocket_connections_total.inc()
    _publish_snapshot()


def record_reconnect_attempt() -> None:
    """Increment reconnect counter and publish an update."""
    websocket_reconnect_attempts_total.inc()
    _publish_snapshot()


def record_ping_failure() -> None:
    """Increment ping failure counter and publish an update."""
    websocket_ping_failures_total.inc()
    _publish_snapshot()


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
    "set_event_bus",
    "record_connection",
    "record_reconnect_attempt",
    "record_ping_failure",
    "start_metrics_server",
]
