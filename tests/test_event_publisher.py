import importlib
import sys
import types
from pathlib import Path
from tests.import_helpers import safe_import, import_optional

safe_import('flask_caching', types.SimpleNamespace(Cache=object))
flask_stub = types.ModuleType("flask")
flask_stub.request = types.SimpleNamespace()
flask_stub.url_for = lambda *a, **k: ""
safe_import('flask', flask_stub)
dash_stub = sys.modules.get("dash", types.ModuleType("dash"))
dash_stub.no_update = getattr(dash_stub, "no_update", object())
dash_stub.dash_table = getattr(dash_stub, "dash_table", types.ModuleType("dash_table"))
safe_import('dash', dash_stub)
safe_import('dash.dash', dash_stub)
safe_import('dash.html', types.ModuleType("dash.html"))
safe_import('dash.dcc', types.ModuleType("dash.dcc"))
safe_import('dash.dependencies', types.ModuleType("dash.dependencies"))
safe_import('dash._callback', types.ModuleType("dash._callback"))
safe_import('dash.dash_table', types.ModuleType("dash_table"))
safe_import('chardet', types.ModuleType("chardet"))

services_stub = types.ModuleType("services")
services_stub.__path__ = [str(Path(__file__).resolve().parents[1] / "services")]
safe_import('services', services_stub)
publish_event = importlib.import_module("services.event_publisher").publish_event

from yosai_intel_dashboard.src.services.event_publisher import publish_event


class DummyBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type: str, data, source=None):
        self.events.append((event_type, data))


class FailingBus(DummyBus):
    def publish(self, event_type: str, data, source=None):
        raise RuntimeError("boom")


def test_publish_event_success():
    bus = DummyBus()
    publish_event(bus, {"a": 1}, event="evt")
    assert bus.events == [("evt", {"a": 1})]


def test_publish_event_no_bus():
    # should not raise
    publish_event(None, {"a": 1})


def test_publish_event_handles_error(caplog):
    bus = FailingBus()
    import logging

    caplog.set_level(logging.DEBUG)
    publish_event(bus, {"a": 1})
    assert not bus.events
    assert any("Event bus publish failed" in rec.message for rec in caplog.records)
