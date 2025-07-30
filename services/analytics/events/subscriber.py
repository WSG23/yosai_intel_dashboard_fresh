from __future__ import annotations

"""Event subscription helper."""

from typing import Any

from core.protocols import EventBusProtocol


class Subscriber:
    """Simple subscriber wrapper."""

    def __init__(self, bus: EventBusProtocol | None) -> None:
        self.bus = bus

    def subscribe(self, event: str, handler: Any) -> None:
        if self.bus:
            self.bus.subscribe(event, handler)


__all__ = ["Subscriber"]
