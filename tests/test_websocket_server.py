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


def _load_server():
    pkg_names = [
        "yosai_intel_dashboard",
        "yosai_intel_dashboard.src",
        "yosai_intel_dashboard.src.core",
    ]
    for name in pkg_names:
        sys.modules.setdefault(name, types.ModuleType(name))
    events_mod = types.ModuleType("yosai_intel_dashboard.src.core.events")

    class EventBus:
        def __init__(self, *a, **kw):
            pass

        def emit(self, *a, **kw):
            pass

        def subscribe(self, event_type, handler):
            return handler

        def unsubscribe(self, token):
            pass

    events_mod.EventBus = EventBus
    sys.modules["yosai_intel_dashboard.src.core.events"] = events_mod
    path = (
        Path(__file__).resolve().parents[1]
        / "yosai_intel_dashboard"
        / "src"
        / "services"
        / "websocket_server.py"
    )
    spec = importlib.util.spec_from_file_location(
        "yosai_intel_dashboard.src.services.websocket_server",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module.AnalyticsWebSocketServer


AnalyticsWebSocketServer = _load_server()


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



class DummyBus:
    def __init__(self) -> None:
        self.subs = {}

    def emit(self, event_type, data):
        for h in self.subs.get(event_type, []):
            h(data)

    def subscribe(self, event_type, handler):
        self.subs.setdefault(event_type, []).append(handler)
        return handler

    def unsubscribe(self, token):
        for handlers in self.subs.values():
            if token in handlers:
                handlers.remove(token)
                break


def _create_server(event_bus: DummyBus) -> AnalyticsWebSocketServer:
    # avoid starting actual websocket server
    original = AnalyticsWebSocketServer._run
    AnalyticsWebSocketServer._run = lambda self: None  # type: ignore
    cfg = ConfigService({
        'metrics_interval': 0.01,
        'ping_interval': 0.01,
        'ping_timeout': 0.01,
    })
    server = AnalyticsWebSocketServer(event_bus, config=cfg)
    AnalyticsWebSocketServer._run = original
    return server


class DummyPool:
    async def release(self, ws):
        pass


def test_ping_client_publishes_alive():
    bus = DummyBus()
    events = []
    bus.subscribe("websocket_heartbeat", lambda d: events.append(d))
    server = _create_server(bus)
    ws = DummyWS(True)
    asyncio.run(server._ping_client(ws))
    assert events and events[0]["status"] == "alive"


def test_ping_client_closes_on_timeout():
    bus = DummyBus()
    events = []
    bus.subscribe("websocket_heartbeat", lambda d: events.append(d))
    server = _create_server(bus)
    ws = DummyWS(False)
    server.clients.add(ws)  # ensure removal
    start = websocket_metrics.websocket_ping_failures_total._value.get()
    asyncio.run(server._ping_client(ws))
    assert events and events[0]["status"] == "timeout"
    assert ws.closed
    assert ws not in server.clients


def _run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def test_stop_closes_clients_and_releases_pool():
    bus = DummyBus()
    server = _create_server(bus)
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
    bus = DummyBus()
    server = _create_server(bus)
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

