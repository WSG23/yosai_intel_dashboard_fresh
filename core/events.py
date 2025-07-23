"""Simple in-memory event bus implementing ``EventBusProtocol``."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from .base_model import BaseModel
from .protocols import EventBusProtocol


class EventBus(BaseModel, EventBusProtocol):
    """In-memory pub/sub event bus."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self._subscribers: Dict[str, List[tuple[str, Callable]]] = {}
        self._history: List[Dict[str, Any]] = []
        self._counter = 0

    def publish(
        self, event_type: str, data: Dict[str, Any], source: str | None = None
    ) -> None:
        self._history.append({"type": event_type, "data": data, "source": source})
        for _sid, handler in self._subscribers.get(event_type, []):
            handler(data)

    def subscribe(self, event_type: str, handler: Callable, priority: int = 0) -> str:
        self._counter += 1
        sid = f"sub-{self._counter}"
        self._subscribers.setdefault(event_type, []).append((sid, handler))
        return sid

    def unsubscribe(self, subscription_id: str) -> None:
        for handlers in self._subscribers.values():
            for sid, func in list(handlers):
                if sid == subscription_id:
                    handlers.remove((sid, func))
                    return

    def get_subscribers(self, event_type: str | None = None) -> List[Dict[str, Any]]:
        if event_type:
            handlers = self._subscribers.get(event_type, [])
            return [{"id": sid, "handler": h} for sid, h in handlers]
        all_handlers: List[Dict[str, Any]] = []
        for etype, handlers in self._subscribers.items():
            for sid, h in handlers:
                all_handlers.append({"id": sid, "handler": h, "type": etype})
        return all_handlers

    def get_event_history(
        self, event_type: str | None = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        history = (
            self._history
            if event_type is None
            else [e for e in self._history if e["type"] == event_type]
        )
        return history[-limit:]
