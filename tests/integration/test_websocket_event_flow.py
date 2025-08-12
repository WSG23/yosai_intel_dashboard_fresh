import asyncio
import importlib.util
import json
import sys
import types
import time
from collections import deque
from pathlib import Path
from typing import Any

import pytest
import websockets
from src.common.config import ConfigService
from shared.events.names import EventName


def _load_server():
    root = Path(__file__).resolve().parents[2]
    pkg_paths = {
        "yosai_intel_dashboard": root / "yosai_intel_dashboard",
        "yosai_intel_dashboard.src": root / "yosai_intel_dashboard" / "src",
        "yosai_intel_dashboard.src.core": root / "yosai_intel_dashboard" / "src" / "core",
        "yosai_intel_dashboard.src.core.interfaces": root / "yosai_intel_dashboard" / "src" / "core" / "interfaces",
        "yosai_intel_dashboard.src.services": root / "yosai_intel_dashboard" / "src" / "services",
    }
    for name, path in pkg_paths.items():
        module = types.ModuleType(name)
        module.__path__ = [str(path)]  # treat as package
        sys.modules.setdefault(name, module)

    events_mod = types.ModuleType("yosai_intel_dashboard.src.core.events")

    class EventBus:
        def __init__(self):
            self._subs: dict[str, list] = {}

        def emit(self, event_type: str, data: dict) -> None:
            for handler in self._subs.get(event_type, []):
                handler(data)

        def subscribe(self, event_type: str, handler, priority: int = 0) -> str:
            self._subs.setdefault(event_type, []).append(handler)
            return handler

        def unsubscribe(self, token: Any) -> None:
            for handlers in self._subs.values():
                if token in handlers:
                    handlers.remove(token)
                    break

    events_mod.EventBus = EventBus
    sys.modules["yosai_intel_dashboard.src.core.events"] = events_mod

    ws_path = pkg_paths["yosai_intel_dashboard.src.services"] / "websocket_server.py"
    spec = importlib.util.spec_from_file_location(
        "yosai_intel_dashboard.src.services.websocket_server", ws_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]

    async def _broadcast_async(self, message: str) -> None:
        for ws in set(self.clients):
            try:
                await ws.send(message)
            except Exception:
                self.clients.discard(ws)

    module.AnalyticsWebSocketServer._broadcast_async = _broadcast_async
    return module, module.AnalyticsWebSocketServer, events_mod.EventBus


ws_module, AnalyticsWebSocketServer, EventBus = _load_server()


@pytest.fixture
def websocket_server():
    event_bus = EventBus()
    cfg = ConfigService({'metrics_interval':0.01,'ping_interval':0.01,'ping_timeout':0.01})
    server = AnalyticsWebSocketServer(event_bus=event_bus, host="127.0.0.1", port=8770, config=cfg)
    server.pool = ws_module.WebSocketConnectionPool()
    server._queue = deque()
    time.sleep(0.05)
    try:
        yield event_bus
    finally:
        server.stop()


@pytest.mark.asyncio
async def test_websocket_event_flow(websocket_server):
    await asyncio.sleep(0.05)
    async with websockets.connect("ws://127.0.0.1:8770") as ws:
        await asyncio.sleep(0.05)
        payload = {"value": 42}
        websocket_server.emit(EventName.ANALYTICS_UPDATE, payload)
        message = await asyncio.wait_for(ws.recv(), timeout=5)
        assert json.loads(message) == payload
