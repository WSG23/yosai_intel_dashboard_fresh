from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import time
import types
from pathlib import Path


class DummyEventBus:
    def __init__(self) -> None:
        self._subs: list[tuple[str, callable]] = []
        self._history: list[dict] = []

    def publish(self, event_type: str, data: dict, source: str | None = None) -> None:
        self._history.append({"type": event_type, "data": data, "source": source})
        for etype, handler in list(self._subs):
            if etype == event_type:
                handler(data)

    def subscribe(self, event_type: str, handler, priority: int = 0) -> str:
        self._subs.append((event_type, handler))
        return f"sub-{len(self._subs)}"

    def unsubscribe(self, sub_id: str) -> None:  # pragma: no cover - simple stub
        pass

    def get_event_history(
        self, event_type: str | None = None, limit: int = 100
    ) -> list[dict]:
        history = (
            self._history
            if event_type is None
            else [e for e in self._history if e["type"] == event_type]
        )
        return history[-limit:]


# Stub package hierarchy to avoid heavy imports from the real package
root_pkg = types.ModuleType("yosai_intel_dashboard")
root_pkg.__path__ = []
src_pkg = types.ModuleType("yosai_intel_dashboard.src")
src_pkg.__path__ = []
core_pkg = types.ModuleType("yosai_intel_dashboard.src.core")
core_pkg.__path__ = []
events_module = types.ModuleType("yosai_intel_dashboard.src.core.events")
events_module.EventBus = DummyEventBus

services_pkg = types.ModuleType("yosai_intel_dashboard.src.services")
services_pkg.__path__ = [
    str(
        Path(__file__).resolve().parents[2]
        / "yosai_intel_dashboard"
        / "src"
        / "services"
    )
]

sys.modules["yosai_intel_dashboard"] = root_pkg
sys.modules["yosai_intel_dashboard.src"] = src_pkg
sys.modules["yosai_intel_dashboard.src.core"] = core_pkg
sys.modules["yosai_intel_dashboard.src.core.events"] = events_module
sys.modules["yosai_intel_dashboard.src.services"] = services_pkg

# Load the websocket server module directly
spec = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.services.websocket_server",
    "yosai_intel_dashboard/src/services/websocket_server.py",
)
ws_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = ws_module
spec.loader.exec_module(ws_module)
AnalyticsWebSocketServer = ws_module.AnalyticsWebSocketServer
EventBus = ws_module.EventBus  # type: ignore


def _run_client(port: int, expected: int) -> list[dict]:
    async def _run() -> list[dict]:
        import websockets

        received: list[dict] = []
        async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
            for _ in range(expected):
                msg = await asyncio.wait_for(ws.recv(), timeout=1)
                if isinstance(msg, bytes):
                    import gzip

                    msg = gzip.decompress(msg).decode("utf-8")
                received.append(json.loads(msg))
        return received

    return asyncio.run(_run())


def test_buffered_events_flushed_on_client_connect() -> None:
    event_bus = EventBus()
    server = AnalyticsWebSocketServer(
        event_bus=event_bus, host="127.0.0.1", port=8766, queue_size=10
    )

    time.sleep(0.1)

    for i in range(3):
        event_bus.publish("analytics_update", {"idx": i})

    messages = _run_client(8766, 3)
    assert [m["idx"] for m in messages] == [0, 1, 2]

    history = event_bus.get_event_history("analytics_update")
    assert len(history) == 6  # original 3 + republished 3

    server.stop()


def test_queue_bound() -> None:
    event_bus = EventBus()
    server = AnalyticsWebSocketServer(
        event_bus=event_bus, host="127.0.0.1", port=8767, queue_size=2
    )

    time.sleep(0.1)

    for i in range(3):
        event_bus.publish("analytics_update", {"idx": i})

    messages = _run_client(8767, 2)
    assert [m["idx"] for m in messages] == [1, 2]

    history = event_bus.get_event_history("analytics_update")
    assert len(history) == 5  # initial 3 + republished 2

    server.stop()


def test_compressed_broadcast() -> None:
    event_bus = EventBus()
    server = AnalyticsWebSocketServer(
        event_bus=event_bus,
        host="127.0.0.1",
        port=8768,
        compression_threshold=10,
    )

    time.sleep(0.1)

    payload = {"data": "x" * 100}
    event_bus.publish("analytics_update", payload)

    messages = _run_client(8768, 1)
    assert messages[0] == payload

    server.stop()
