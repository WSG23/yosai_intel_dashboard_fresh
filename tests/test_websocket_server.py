from __future__ import annotations

import asyncio
import importlib.util
import sys
import threading
import types
from collections import deque
from pathlib import Path
import threading

from src.websocket import metrics as websocket_metrics
from src.common.config import ConfigService
from yosai_intel_dashboard.src.services.websocket_server import AnalyticsWebSocketServer
from yosai_intel_dashboard.src.infrastructure.callbacks import (
    CallbackType,
    register_callback,
    unregister_callback,
)


class DummyWS:
    def __init__(self, respond: bool = True):
        self.respond = respond
        self.closed = False
        self.messages = []

    def ping(self):
        fut = asyncio.Future()
        if self.respond:
            fut.set_result(None)
        return fut

    async def close(self):
        self.closed = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration



def _create_server() -> AnalyticsWebSocketServer:
    # avoid starting actual websocket server
    original = AnalyticsWebSocketServer._run
    AnalyticsWebSocketServer._run = lambda self: None  # type: ignore
    cfg = ConfigService({
        'metrics_interval': 0.01,
        'ping_interval': 0.01,
        'ping_timeout': 0.01,
    })
    server = AnalyticsWebSocketServer(config=cfg)
    AnalyticsWebSocketServer._run = original
    return server


class DummyPool:
    async def release(self, ws):
        pass


def test_ping_client_publishes_alive():
    events: list[dict] = []

    def handler(data):
        events.append(data)

    register_callback(CallbackType.WEBSOCKET_HEARTBEAT, handler, component_id="test")
    server = _create_server()
    ws = DummyWS(True)
    asyncio.run(server._ping_client(ws))
    assert events and events[0]["status"] == "alive"
    unregister_callback(CallbackType.WEBSOCKET_HEARTBEAT, handler)


def test_ping_client_closes_on_timeout():
    events: list[dict] = []

    def handler(data):
        events.append(data)

    register_callback(CallbackType.WEBSOCKET_HEARTBEAT, handler, component_id="test")
    server = _create_server()
    ws = DummyWS(False)
    server.clients.add(ws)  # ensure removal
    start = websocket_metrics.websocket_ping_failures_total._value.get()
    asyncio.run(server._ping_client(ws))
    assert events and events[0]["status"] == "timeout"
    assert ws.closed
    assert ws not in server.clients
    unregister_callback(CallbackType.WEBSOCKET_HEARTBEAT, handler)


def _run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def test_stop_closes_clients_and_releases_pool():
    server = _create_server()
    loop = asyncio.new_event_loop()
    server._loop = loop
    server._thread = threading.Thread(target=_run_loop, args=(loop,), daemon=True)
    server._thread.start()
    ws = DummyWS()
    server.clients.add(ws)
    asyncio.run_coroutine_threadsafe(server.pool.acquire(ws), loop).result()
    server._queue.append({"queued": True})
    server.stop()
    loop.close()
    assert ws.closed
    assert len(server.clients) == 0
    assert len(server.pool) == 0
    assert not server._queue


def test_stop_cancels_heartbeat_task():
    server = _create_server()
    loop = asyncio.new_event_loop()
    server._loop = loop
    server._thread = threading.Thread(target=_run_loop, args=(loop,), daemon=True)
    server._thread.start()

    async def create_task():
        return asyncio.create_task(asyncio.sleep(3600))

    server._heartbeat_task = asyncio.run_coroutine_threadsafe(create_task(), loop).result()

    server.stop()
    loop.close()
    assert server._heartbeat_task is None

