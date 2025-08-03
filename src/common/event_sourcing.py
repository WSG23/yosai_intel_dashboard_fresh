"""Lightweight in-memory event sourced store."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class Event:
    """Represents a single state change."""

    key: str
    value: Any


class EventLog:
    """Append-only log of events."""

    def __init__(self) -> None:
        self._events: List[Event] = []

    def append(self, event: Event) -> None:
        self._events.append(event)

    def __iter__(self) -> Iterable[Event]:
        return iter(self._events)

    def clear(self) -> None:
        self._events.clear()


class EventSourcedDict:
    """Dictionary-like store that records all updates as events.

    The current state can always be reconstructed by replaying the stored
    events. ``rebuild`` applies all logged events to rebuild the in-memory
    state, which is useful after process restarts or when the state instance
    is otherwise lost.
    """

    def __init__(self, log: EventLog | None = None) -> None:
        self.log = log or EventLog()
        self._state: Dict[str, Any] = {}
        for event in self.log:
            self._state[event.key] = event.value

    def set(self, key: str, value: Any) -> None:
        event = Event(key=key, value=value)
        self.log.append(event)
        self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def rebuild(self) -> Dict[str, Any]:
        """Rebuild ``_state`` by replaying all events."""
        state: Dict[str, Any] = {}
        for event in self.log:
            state[event.key] = event.value
        self._state = state
        return state


__all__ = ["Event", "EventLog", "EventSourcedDict"]
