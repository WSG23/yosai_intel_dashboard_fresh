from __future__ import annotations

"""Minimal event service adapter for tests.

The real project contains a feature rich implementation.  For the purposes of
unit tests we only need a small subset that exercises the circuit breaker
behaviour when an external dependency is unavailable.
"""

from typing import Any, Dict

from yosai_intel_dashboard.src.services.resilience import (
    CircuitBreaker,
    CircuitBreakerOpen,
)


class EventServiceAdapter:
    """Adapter protecting event processing with a circuit breaker."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or "http://localhost"
        self.kafka_producer = None
        self.circuit_breaker = CircuitBreaker(5, 60, name="event_service")

    async def _process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
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
                    return {"event_id": event.get("event_id"), "status": "accepted"}
                return {"event_id": event.get("event_id"), "status": "sent"}
        except CircuitBreakerOpen:
            return {"event_id": event.get("event_id"), "status": "unavailable"}
