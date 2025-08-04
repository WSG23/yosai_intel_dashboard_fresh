from __future__ import annotations

import asyncio
import gzip
import json
import logging
import threading
from collections import deque
from contextlib import suppress
from typing import Deque, Optional, Set

from websockets import WebSocketServerProtocol, serve

from src.common.base import BaseComponent
from src.common.config import ConfigProvider, ConfigService
from src.websocket import metrics as websocket_metrics
from yosai_intel_dashboard.src.infrastructure.callbacks import (
    CallbackType,
    register_callback,
    unregister_callback,
    trigger_callback,
)

from .websocket_pool import WebSocketConnectionPool

logger = logging.getLogger(__name__)


class AnalyticsWebSocketServer(BaseComponent):
    """Simple WebSocket server broadcasting analytics updates."""

    def __init__(
        self,
        *,
        config: ConfigProvider | None = None,
        host: str = "0.0.0.0",
        port: int = 6789,
        ping_interval: float | None = None,
        ping_timeout: float | None = None,
        queue_size: int = 100,
        compression_threshold: int = 0,
    ) -> None:
        config = config or ConfigService()
        ping_interval = (
            ping_interval if ping_interval is not None else config.ping_interval
        )
        ping_timeout = ping_timeout if ping_timeout is not None else config.ping_timeout
        super().__init__(
            component_id="AnalyticsWebSocketServer",
            config=config,
            host=host,
            port=port,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            queue_size=queue_size,
            compression_threshold=compression_threshold,
        )
        self.clients: Set[WebSocketServerProtocol] = set()
        self.pool = WebSocketConnectionPool()
        self._queue: Deque[dict] = deque(maxlen=queue_size)

        self._loop: asyncio.AbstractEventLoop | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        register_callback(
            CallbackType.ANALYTICS_UPDATE,
            self.broadcast,
            component_id=self.component_id,
        )
        logger.info("WebSocket server started on ws://%s:%s", self.host, self.port)

    async def _handler(self, websocket: WebSocketServerProtocol) -> None:
        await self.pool.acquire(websocket)
        self.clients.add(websocket)
        websocket_metrics.record_connection()

        if self._queue:
            queued = list(self._queue)
            self._queue.clear()
            for event in queued:
                trigger_callback(CallbackType.ANALYTICS_UPDATE, event)

        try:
            async for _ in websocket:
                pass  # Server is broadcast-only
        except Exception as exc:  # pragma: no cover - connection errors
            logger.debug("WebSocket connection error: %s", exc)
        finally:
            await self.pool.release(websocket)
            self.clients.discard(websocket)

    async def _serve(self) -> None:
        self._loop = asyncio.get_running_loop()
        async with serve(self._handler, self.host, self.port):
            self._heartbeat_task = asyncio.create_task(self._heartbeat())

            await asyncio.Event().wait()

    async def _ping_client(self, ws: WebSocketServerProtocol) -> None:
        try:
            pong_waiter = ws.ping()
            await asyncio.wait_for(pong_waiter, timeout=self.ping_timeout)
            trigger_callback(
                CallbackType.WEBSOCKET_HEARTBEAT,
                {"client": id(ws), "status": "alive"},
            )
        except asyncio.TimeoutError:
            websocket_metrics.record_ping_failure()
            trigger_callback(
                CallbackType.WEBSOCKET_HEARTBEAT,
                {"client": id(ws), "status": "timeout"},
            )
            try:
                await ws.close()
            finally:
                self.clients.discard(ws)
        except Exception:  # pragma: no cover - connection closed or other errors
            self.clients.discard(ws)

    async def _heartbeat(self) -> None:
        while True:
            await asyncio.sleep(self.ping_interval)
            for ws in set(self.clients):
                await self._ping_client(ws)

    def _run(self) -> None:
        try:
            asyncio.run(self._serve())
        except RuntimeError:
            # Event loop stopped before coroutine completed
            pass

    def broadcast(self, data: dict) -> None:
        if self.clients:
            message = json.dumps(data)
            if self.compression_threshold and len(message) > self.compression_threshold:
                payload: bytes | str = gzip.compress(message.encode("utf-8"))
            else:
                payload = message
            if self._loop is not None:
                asyncio.run_coroutine_threadsafe(
                    self.pool.broadcast(payload), self._loop
                )
        else:
            self._queue.append(data)

    async def _broadcast_async(self, message: str) -> None:
        await self.pool.broadcast(message)

    def stop(self) -> None:
        """Stop the server thread and event loop."""
        unregister_callback(CallbackType.ANALYTICS_UPDATE, self.broadcast)
        if self._loop is not None:

            async def _shutdown() -> None:
                for ws in list(self.clients):
                    try:
                        await ws.close()
                    finally:
                        await self.pool.release(ws)
                self.clients.clear()
                self._queue.clear()
                if self._heartbeat_task is not None:
                    self._heartbeat_task.cancel()
                    with suppress(asyncio.CancelledError):
                        await self._heartbeat_task
                    self._heartbeat_task = None

            asyncio.run_coroutine_threadsafe(_shutdown(), self._loop).result()

            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=1)


__all__ = ["AnalyticsWebSocketServer"]
