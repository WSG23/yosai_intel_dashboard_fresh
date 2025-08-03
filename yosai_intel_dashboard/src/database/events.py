"""Lightweight storage for normalized events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class EventRecord:
    """Normalized event data."""

    name: str
    start: datetime
    category: str


_store: List[EventRecord] = []


def add_events(events: List[EventRecord]) -> None:
    """Persist a batch of events in memory."""
    _store.extend(events)


def list_events() -> List[EventRecord]:
    """Return all stored events."""
    return list(_store)
