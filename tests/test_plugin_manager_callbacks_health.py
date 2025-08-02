import importlib
import pathlib
import sys

import pytest

# Import real Flask even when stubs shadow it on PYTHONPATH
Flask = None
stub_path = None
for p in list(sys.path):
    if p.endswith("tests/stubs"):
        sys.path.remove(p)
        stub_path = p
        break
try:
    from flask import Flask as RealFlask

    Flask = RealFlask
finally:
    if stub_path:
        sys.path.insert(0, stub_path)

from config import create_config_manager
from yosai_intel_dashboard.src.core.plugins.manager import PluginManager
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from tests.utils.plugin_package_builder import PluginPackageBuilder


class DummyDash:
    """Minimal Dash substitute with Flask server."""

    def __init__(self, server: Flask) -> None:
        self.server = server

    def callback(self, *args, **kwargs):
        def decorator(func):
            return func

        return decorator


@pytest.mark.usefixtures("fake_dash")
def test_callbacks_and_health_endpoint(monkeypatch, tmp_path):
    with PluginPackageBuilder(tmp_path) as builder:
        sys.path.insert(0, str(tmp_path))
        manager = None
        try:
            cfg = create_config_manager()
            cfg.config.plugin_settings[builder.plugin_name] = {"enabled": True}
            manager = PluginManager(
                ServiceContainer(),
                cfg,
                package=builder.package_name,
                health_check_interval=1,
            )
            manager.load_all_plugins()

            flask_app = Flask(__name__)
            dash_app = DummyDash(flask_app)
            coord = TrulyUnifiedCallbacks(dash_app)
            manager.register_plugin_callbacks(dash_app, coord)

            assert builder.callback_id in coord.registered_callbacks
            routes = [r.rule for r in flask_app.url_map.iter_rules()]
            assert "/health/plugins" in routes

            client = flask_app.test_client()
            resp = client.get("/health/plugins")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data[builder.plugin_name]["health"]["healthy"] is True
        finally:
            sys.path.remove(str(tmp_path))
            if manager:
                manager.stop_health_monitor()
