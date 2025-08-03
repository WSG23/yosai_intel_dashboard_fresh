from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections import deque
from typing import Optional, Set, Deque


from websockets import WebSocketServerProtocol, serve

from yosai_intel_dashboard.src.core.events import EventBus
from src.websocket import metrics as websocket_metrics

from .websocket_pool import WebSocketConnectionPool

logger = logging.getLogger(__name__)


class AnalyticsWebSocketServer:
    """Simple WebSocket server broadcasting analytics updates."""

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        host: str = "0.0.0.0",
        port: int = 6789,
        queue_size: int = 100,
    ) -> None:
        self.host = host
        self.port = port
        self.event_bus = event_bus or EventBus()
        self.clients: Set[WebSocketServerProtocol] = set()
        self._queue: Deque[dict] = deque(maxlen=queue_size)

        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._subscription_id: str | None = None
        self._thread.start()
        if self.event_bus:
            self._subscription_id = self.event_bus.subscribe(
                "analytics_update", self.broadcast
            )
        logger.info("WebSocket server started on ws://%s:%s", self.host, self.port)

    async def _handler(self, websocket: WebSocketServerProtocol) -> None:
        self.clients.add(websocket)
        if self._queue:
            queued = list(self._queue)
            self._queue.clear()
            for event in queued:
                if self.event_bus:
                    self.event_bus.publish("analytics_update", event)

        try:
            async for _ in websocket:
                pass  # Server is broadcast-only
        except Exception as exc:  # pragma: no cover - connection errors
            logger.debug("WebSocket connection error: %s", exc)
        finally:
            await self.pool.release(websocket)

    async def _serve(self) -> None:
        self._loop = asyncio.get_running_loop()
        async with serve(self._handler, self.host, self.port, compression="deflate"):
            await asyncio.Event().wait()

    def _run(self) -> None:
        try:
            asyncio.run(self._serve())
        except RuntimeError:
            # Event loop stopped before coroutine completed
            pass

    def broadcast(self, data: dict) -> None:
        if self.clients:
            message = json.dumps(data)
            if self._loop is not None:
                asyncio.run_coroutine_threadsafe(
                    self._broadcast_async(message), self._loop
                )
        else:
            self._queue.append(data)


    def stop(self) -> None:
        """Stop the server thread and event loop."""
        if self.event_bus and self._subscription_id:
            self.event_bus.unsubscribe(self._subscription_id)
            self._subscription_id = None
        if self._loop is not None:
            future = asyncio.run_coroutine_threadsafe(self._close_clients(), self._loop)
            try:
                future.result(timeout=1)
            except Exception as exc:  # pragma: no cover - timeout or loop issues
                logger.debug("Error waiting for client close: %s", exc)
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=1)


__all__ = ["AnalyticsWebSocketServer"]
