# flake8: noqa: E402
from __future__ import annotations

import asyncio
import json
import shutil
import sys
import threading
import types

import dash
import dash_bootstrap_components as dbc
import pytest
from dash import dcc, html

# Stub heavy optional analytics dependencies
for _mod in (
    "scipy",
    "sklearn",
    "sklearn.ensemble",
    "sklearn.exceptions",
    "sklearn.preprocessing",
    "sklearn.cluster",
    "sklearn.neural_network",
):
    sys.modules.setdefault(_mod, types.ModuleType(_mod))
if "scipy" not in sys.modules:
    sys.modules["scipy"] = types.ModuleType("scipy")
sys.modules.setdefault("scipy.stats", types.ModuleType("scipy.stats"))
sys.modules["scipy"].stats = sys.modules["scipy.stats"]

from config import create_config_manager
from core.events import EventBus
from core.plugins.auto_config import setup_plugins
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder

pytestmark = pytest.mark.usefixtures("fake_dash", "fake_dbc")


@pytest.fixture
def _skip_if_no_chromedriver() -> None:
    if not shutil.which("chromedriver"):
        pytest.skip("chromedriver not installed")


def _build_plugin(tmp_path):
    pkg = tmp_path / "sample_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    plugin_code = """
from dash import Output, Input
from dash.exceptions import PreventUpdate
from core.protocols.plugin import PluginMetadata
from core.plugins.callback_unifier import CallbackUnifier

class SamplePlugin:
    metadata = PluginMetadata(
        name="sample_plugin",
        version="0.1",
        description="sample plugin",
        author="tester",
    )
    def __init__(self):
        self.called = False
    def load(self, container, config):
        self.event_bus = container.get("event_bus")
        return True
    def configure(self, config):
        return True
    def start(self):
        return True
    def stop(self):
        return True
    def health_check(self):
        return {"healthy": True}
    def register_callbacks(self, manager, container):
        event_bus = container.get("event_bus")
        @CallbackUnifier(manager)(
            Output("plugin-output", "children"),
            Input("drag-drop-upload", "filename"),
            Input("drag-drop-upload", "contents"),
            callback_id="plugin_upload_cb",
            component_name="SamplePlugin",
            prevent_initial_call=True,
        )
        def handle_upload(filename, contents):
            if not contents:
                raise PreventUpdate
            event_bus.publish("analytics_update", {"file": filename})
            self.called = True
            return f"plugin:{filename}"
        return True

def create_plugin():
    return SamplePlugin()
"""
    (pkg / "plug.py").write_text(plugin_code)
    return pkg


def _create_app(monkeypatch, container, config, package_name):
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    coord = TrulyUnifiedCallbacks(app)
    dummy_mod = types.ModuleType(
        "yosai_intel_dashboard.src.components.analytics.real_time_dashboard"
    )
    dummy_mod.RealTimeAnalytics = object
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.components.analytics.real_time_dashboard",
        dummy_mod,
    )
    from yosai_intel_dashboard.src.components.file_upload_component import (
        FileUploadComponent,
    )

    comp = FileUploadComponent()
    comp.register_callbacks(coord)
    app.layout = html.Div(
        [dcc.Location(id="url"), comp.layout(), html.Div(id="plugin-output")]
    )
    setup_plugins(app, container=container, config_manager=config, package=package_name)
    return app


@pytest.mark.integration
def test_plugin_upload_event_sse_ws(
    _skip_if_no_chromedriver, dash_duo, tmp_path, monkeypatch
):
    _build_plugin(tmp_path)
    sys.path.insert(0, str(tmp_path))
    container = ServiceContainer()
    event_bus = EventBus()
    container.register("event_bus", event_bus)
    cfg = create_config_manager()
    cfg.config.plugin_settings["sample_plugin"] = {"enabled": True}

    from services.websocket_server import AnalyticsWebSocketServer

    ws_server = AnalyticsWebSocketServer(
        event_bus=event_bus, host="127.0.0.1", port=8765
    )

    messages: list[str] = []

    def _client():
        async def _run():
            import websockets

            async with websockets.connect("ws://127.0.0.1:8765") as ws:
                msg = await ws.recv()
                messages.append(msg)

        asyncio.run(_run())

    t = threading.Thread(target=_client, daemon=True)
    t.start()

    app = _create_app(monkeypatch, container, cfg, "sample_pkg")
    csv = (
        UploadFileBuilder()
        .with_dataframe(DataFrameBuilder().add_column("a", [1, 2]).build())
        .write_csv(tmp_path / "sample.csv")
    )
    dash_duo.start_server(app)
    file_input = dash_duo.find_element("#drag-drop-upload input")
    file_input.send_keys(str(csv))
    dash_duo.wait_for_text_to_equal("#upload-progress", "100%", timeout=10)
    dash_duo.wait_for_text_to_equal("#plugin-output", f"plugin:{csv.name}", timeout=10)
    logs = dash_duo.driver.execute_script("return window.uploadProgressLog.length")
    t.join(timeout=5)

    assert logs and logs > 3
    events = event_bus.get_event_history("analytics_update")
    assert events and events[-1]["data"]["file"] == "sample.csv"
    assert messages and json.loads(messages[0])["file"] == "sample.csv"

    ws_server._loop.call_soon_threadsafe(ws_server._loop.stop)
    ws_server._thread.join(timeout=1)
    sys.path.remove(str(tmp_path))
