"""Lightweight storage for normalized events."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class EventRecord:
    """Normalized event data."""

    name: str
    start: datetime
    category: str


_store: List[EventRecord] = []
# Index events by category for faster lookups
_by_category: Dict[str, List[EventRecord]] = defaultdict(list)


def add_events(events: List[EventRecord]) -> None:
    """Persist a batch of events in memory."""
    _store.extend(events)
    for event in events:
        _by_category[event.category].append(event)


def list_events() -> List[EventRecord]:
    """Return all stored events."""
    return list(_store)


def get_events_by_category(category: str) -> List[EventRecord]:
    """Return events filtered by *category* using the category index."""
    return list(_by_category.get(category, []))


def clear_events() -> None:
    """Remove all stored events.

    This helper is primarily intended for tests to ensure a clean
    state between runs without having to reach into module internals.
    """
    _store.clear()
    _by_category.clear()
