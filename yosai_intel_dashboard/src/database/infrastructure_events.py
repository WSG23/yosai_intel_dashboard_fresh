"""Simple in-memory store for infrastructure events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class InfrastructureEvent:
    """Represents an infrastructure outage or degradation."""

    source: str
    description: str
    start_time: datetime
    end_time: Optional[datetime] = None


_EVENTS: List[InfrastructureEvent] = []


def record_event(event: InfrastructureEvent) -> None:
    """Store *event* in the in-memory event list."""
    _EVENTS.append(event)


def get_active_events(at: Optional[datetime] = None) -> List[InfrastructureEvent]:
    """Return events active at time *at* (or now if not provided)."""
    now = at or datetime.utcnow()
    return [
        e
        for e in _EVENTS
        if e.start_time <= now and (e.end_time is None or e.end_time >= now)
    ]


def clear_events() -> None:
    """Remove all stored events (useful for tests)."""
    _EVENTS.clear()


__all__ = ["InfrastructureEvent", "record_event", "get_active_events", "clear_events"]
