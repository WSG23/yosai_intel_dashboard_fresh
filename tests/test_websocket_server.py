import asyncio
import importlib.util
import sys
import types
from pathlib import Path


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
        def publish(self, *a, **kw):
            pass
        def subscribe(self, *a, **kw):
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

    def ping(self):
        fut = asyncio.Future()
        if self.respond:
            fut.set_result(None)
        return fut

    async def close(self):
        self.closed = True


class DummyBus:
    def __init__(self) -> None:
        self.subs = {}
    def publish(self, event_type, data):
        for h in self.subs.get(event_type, []):
            h(data)
    def subscribe(self, event_type, handler):
        self.subs.setdefault(event_type, []).append(handler)


def _create_server(event_bus: DummyBus) -> AnalyticsWebSocketServer:
    # avoid starting actual websocket server
    original = AnalyticsWebSocketServer._run
    AnalyticsWebSocketServer._run = lambda self: None  # type: ignore
    server = AnalyticsWebSocketServer(event_bus, ping_interval=0.01, ping_timeout=0.01)
    AnalyticsWebSocketServer._run = original
    return server


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
    asyncio.run(server._ping_client(ws))
    assert events and events[0]["status"] == "timeout"
    assert ws.closed
    assert ws not in server.clients
