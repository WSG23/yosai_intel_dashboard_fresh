from __future__ import annotations

import asyncio
import logging
from typing import Set

from websockets import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class WebSocketConnectionPool:
    """Pool managing active ``WebSocketServerProtocol`` connections.

    Connections are added to the pool when acquired and removed when released.
    The pool can broadcast a message to all active connections, removing any
    dead ones encountered during send operations.
    """

    def __init__(self) -> None:
        self._connections: Set[WebSocketServerProtocol] = set()
        self._lock = asyncio.Lock()

    async def acquire(self, websocket: WebSocketServerProtocol) -> None:
        """Add a websocket connection to the pool."""
        async with self._lock:
            self._connections.add(websocket)

    async def release(self, websocket: WebSocketServerProtocol) -> None:
        """Remove a websocket connection from the pool."""
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: str) -> None:
        """Broadcast ``message`` to all active connections."""
        async with self._lock:
            connections = set(self._connections)
        for ws in connections:
            try:
                await ws.send(message)
            except Exception as exc:  # pragma: no cover - network errors
                logger.debug("Dropping websocket due to send error: %s", exc)
                await self.release(ws)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._connections)


__all__ = ["WebSocketConnectionPool"]
