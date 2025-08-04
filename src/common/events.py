"""Thread-safe in-memory event bus and publisher utilities."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from types import MappingProxyType
from typing import Any, Callable, Dict, List, Mapping
import warnings


@dataclass(frozen=True)
class Event:
    """Immutable event record stored by :class:`EventBus`."""

    type: str
    data: Mapping[str, Any]


class EventBus:
    """Simple thread-safe event bus.

    Subscribers are stored by event type. ``emit`` makes a defensive copy of
    the payload and exposes it as an immutable mapping to subscribers to avoid
    accidental mutation of shared state.
    """

    __slots__ = ("_subscribers", "_lock", "_counter", "_history")

    def __init__(self) -> None:
        self._subscribers: Dict[str, Dict[str, Callable[[Mapping[str, Any]], None]]] = (
            defaultdict(dict)
        )
        self._lock = RLock()
        self._counter = 0
        self._history: List[Event] = []

    def subscribe(
        self, event_type: str, handler: Callable[[Mapping[str, Any]], None]
    ) -> str:
        """Register ``handler`` to be called when ``event_type`` is emitted.

        Returns a subscription identifier that can be used to unsubscribe later.
        """
        with self._lock:
            self._counter += 1
            token = f"{event_type}:{self._counter}"
            self._subscribers[event_type][token] = handler
            return token

    def unsubscribe(self, token: str) -> None:
        """Remove a previously registered handler using its subscription token."""
        with self._lock:
            for event_type, handlers in list(self._subscribers.items()):
                if token in handlers:
                    del handlers[token]
                    if not handlers:
                        del self._subscribers[event_type]
                    break

    def emit(self, event_type: str, payload: Mapping[str, Any]) -> None:
        """Publish ``payload`` to all subscribers of ``event_type``."""
        with self._lock:
            handlers = list(self._subscribers.get(event_type, {}).values())
        immutable_payload = MappingProxyType(deepcopy(dict(payload)))
        self._history.append(Event(type=event_type, data=immutable_payload))
        for handler in handlers:
            handler(immutable_payload)

    def publish(self, event_type: str, payload: Mapping[str, Any]) -> None:
        """Alias for :meth:`emit` for backwards compatibility."""
        self.emit(event_type, payload)

    def get_event_history(
        self, event_type: str | None = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Return recent events optionally filtered by ``event_type``."""
        history = (
            self._history
            if event_type is None
            else list(filter(lambda e: e.type == event_type, self._history))
        )
        return list(
            map(
                lambda e: {"type": e.type, "data": {k: v for k, v in e.data.items()}},
                history,
            )
        )[-limit:]


class EventPublisher:
    """Mixin providing convenience methods for publishing events.

    The mixin no longer performs its own dependency wiring.  ``event_bus`` and
    any other dependencies should be provided via ``BaseComponent``.  The
    ``__init__`` method remains as a deprecation shim so that existing code
    calling ``super().__init__(event_bus)`` continues to work, but callers are
    encouraged to pass ``event_bus`` through ``BaseComponent.__init__``
    directly.
    """

    def __init__(self, event_bus: EventBus | None = None, **deps: Any) -> None:
        if event_bus is not None or deps:
            warnings.warn(
                "EventPublisher.__init__ is deprecated; pass dependencies via "
                "BaseComponent.__init__ instead",
                DeprecationWarning,
                stacklevel=2,
            )
            if event_bus is not None:
                setattr(self, "event_bus", event_bus)
            for name, value in deps.items():
                setattr(self, name, value)

    def publish_event(self, event_type: str, payload: Mapping[str, Any]) -> None:
        """Publish an event via the configured ``event_bus``."""
        self.event_bus.emit(event_type, payload)


__all__ = ["Event", "EventBus", "EventPublisher"]
