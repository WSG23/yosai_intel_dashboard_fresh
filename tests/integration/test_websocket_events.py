from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest
import websockets


def _load_server():
    pkg_names = [
        "yosai_intel_dashboard",
        "yosai_intel_dashboard.src",
        "yosai_intel_dashboard.src.core",
        "yosai_intel_dashboard.src.core.interfaces",
        "yosai_intel_dashboard.src.services",
    ]
    for name in pkg_names:
        sys.modules.setdefault(name, types.ModuleType(name))

    events_mod = types.ModuleType("yosai_intel_dashboard.src.core.events")

    class DummyEventBus:
        def __init__(self):
            self._subs: dict[str, list] = {}

        def publish(self, event_type: str, data: dict) -> None:
            for handler in self._subs.get(event_type, []):
                handler(data)

        def subscribe(self, event_type: str, handler, priority: int = 0) -> None:
            self._subs.setdefault(event_type, []).append(handler)

        def unsubscribe(self, sub_id: str) -> None:  # pragma: no cover - stub
            pass

    events_mod.EventBus = DummyEventBus
    sys.modules["yosai_intel_dashboard.src.core.events"] = events_mod

    path = (
        Path(__file__).resolve().parents[2]
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
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module.AnalyticsWebSocketServer, events_mod.EventBus


AnalyticsWebSocketServer, EventBus = _load_server()


def test_websocket_events_broadcast():
    event_bus = EventBus()
    server = AnalyticsWebSocketServer(event_bus=event_bus, host="127.0.0.1", port=8766)
    try:

        async def runner():
            async def client():
                await asyncio.sleep(0.05)
                async with websockets.connect("ws://127.0.0.1:8766") as ws:
                    msg = await ws.recv()
                    if isinstance(msg, bytes):
                        import gzip

                        msg = gzip.decompress(msg).decode("utf-8")
                    return json.loads(msg)

            task = asyncio.create_task(client())
            await asyncio.sleep(0.1)
            event_bus.publish("analytics_update", {"value": 42})
            return await asyncio.wait_for(task, timeout=5)

        data = asyncio.run(runner())
        assert data == {"value": 42}
    finally:
        server.stop()
