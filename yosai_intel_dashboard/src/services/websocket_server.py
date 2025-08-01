import asyncio
import json
import logging
import threading
from typing import Optional, Set

from websockets import WebSocketServerProtocol, serve

from yosai_intel_dashboard.src.core.events import EventBus

logger = logging.getLogger(__name__)


class AnalyticsWebSocketServer:
    """Simple WebSocket server broadcasting analytics updates."""

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        host: str = "0.0.0.0",
        port: int = 6789,
    ) -> None:
        self.host = host
        self.port = port
        self.event_bus = event_bus or EventBus()
        self.clients: Set[WebSocketServerProtocol] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if self.event_bus:
            self.event_bus.subscribe("analytics_update", self.broadcast)
        logger.info("WebSocket server started on ws://%s:%s", self.host, self.port)

    async def _handler(self, websocket: WebSocketServerProtocol) -> None:
        self.clients.add(websocket)
        try:
            async for _ in websocket:
                pass  # Server is broadcast-only
        except Exception as exc:  # pragma: no cover - connection errors
            logger.debug("WebSocket connection error: %s", exc)
        finally:
            self.clients.discard(websocket)

    async def _serve(self) -> None:
        self._loop = asyncio.get_running_loop()
        async with serve(self._handler, self.host, self.port):
            await asyncio.Event().wait()

    def _run(self) -> None:
        asyncio.run(self._serve())

    async def _broadcast_async(self, message: str) -> None:
        for ws in set(self.clients):
            try:
                await ws.send(message)
            except Exception as exc:  # pragma: no cover - drop dead clients
                logger.debug("Failed sending to client: %s", exc)
                self.clients.discard(ws)

    def broadcast(self, data: dict) -> None:
        message = json.dumps(data)
        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(self._broadcast_async(message), self._loop)

    def stop(self) -> None:
        """Stop the server thread and event loop."""
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=1)


__all__ = ["AnalyticsWebSocketServer"]
