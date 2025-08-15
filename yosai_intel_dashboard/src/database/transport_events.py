from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterator, List, Optional


@dataclass
class TrafficEvent:
    """Represents a traffic-related event affecting travel time."""

    event_type: str
    location: str
    delay_minutes: int
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


_events: List[TrafficEvent] = []
# Maintain an index of events by location for faster queries
_by_location: Dict[str, List[TrafficEvent]] = defaultdict(list)


def add_event(event: TrafficEvent) -> None:
    """Persist a transport event."""
    _events.append(event)
    _by_location[event.location].append(event)


def get_events(location: Optional[str] = None) -> Iterator[TrafficEvent]:
    """Yield stored events, optionally filtered by location."""
    if location is None:
        return iter(_events)
    return iter(_by_location.get(location, []))


def total_delay(location: str) -> int:
    """Aggregate delay in minutes for a given location."""
    return sum(e.delay_minutes for e in _by_location.get(location, []))


def clear_events() -> None:
    """Clear all stored events (used in tests)."""
    _events.clear()
    _by_location.clear()


__all__ = [
    "TrafficEvent",
    "add_event",
    "get_events",
    "total_delay",
    "clear_events",
]
