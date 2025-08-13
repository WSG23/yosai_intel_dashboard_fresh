"""Minimal event service adapter for tests.

The real project contains a feature rich implementation.  For the purposes of
unit tests we only need a small subset that exercises the circuit breaker
behaviour when an external dependency is unavailable.
"""

from __future__ import annotations

from typing import Mapping, Protocol, TypedDict

from services.resilience import CircuitBreaker, CircuitBreakerOpen
from config.service_discovery import resolve_service


class _KafkaProducer(Protocol):
    def produce(self, topic: str, key: object, value: Mapping[str, object]) -> None:
        ...

    def flush(self, timeout: float) -> None:
        ...


class ProcessedEvent(TypedDict):
    event_id: object | None
    status: str


class EventServiceAdapter:
    """Adapter protecting event processing with a circuit breaker."""

    def __init__(self, base_url: str | None = None) -> None:
        if base_url is None:
            try:
                base_url = f"http://{resolve_service('event-service')}"
            except Exception:
                base_url = "http://localhost"
        self.base_url = base_url
        self.kafka_producer: _KafkaProducer | None = None
        self.circuit_breaker = CircuitBreaker(5, 60, name="event_service")

    async def _process_event(self, event: Mapping[str, object]) -> ProcessedEvent:
        """Process a single event, falling back when the circuit is open."""
        try:
            async with self.circuit_breaker:
                # In tests the producer is always ``None`` so this block is never
                # executed.  The logic is kept for completeness.
                if self.kafka_producer is not None:  # pragma: no cover - not used
                    self.kafka_producer.produce(
                        "access-events", key=event.get("event_id"), value=event
                    )
                    self.kafka_producer.flush(0)
                    return {
                        "event_id": event.get("event_id"),
                        "status": "accepted",
                    }
                return {"event_id": event.get("event_id"), "status": "sent"}
        except CircuitBreakerOpen:
            return {"event_id": event.get("event_id"), "status": "unavailable"}
