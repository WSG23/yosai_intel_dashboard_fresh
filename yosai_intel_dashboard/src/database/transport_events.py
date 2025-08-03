from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class TrafficEvent:
    """Represents a traffic-related event affecting travel time."""

    event_type: str
    location: str
    delay_minutes: int
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


_events: List[TrafficEvent] = []


def add_event(event: TrafficEvent) -> None:
    """Persist a transport event."""
    _events.append(event)


def get_events(location: Optional[str] = None) -> List[TrafficEvent]:
    """Return stored events, optionally filtered by location."""
    events = _events
    if location is not None:
        events = [e for e in events if e.location == location]
    return list(events)


def total_delay(location: str) -> int:
    """Aggregate delay in minutes for a given location."""
    return sum(e.delay_minutes for e in get_events(location))


def clear_events() -> None:
    """Clear all stored events (used in tests)."""
    _events.clear()


__all__ = [
    "TrafficEvent",
    "add_event",
    "get_events",
    "total_delay",
    "clear_events",
]
