import importlib.util
import sys
import time
import types
from pathlib import Path

from src.common.config import ConfigService
from yosai_intel_dashboard.src.infrastructure.callbacks import (
    CallbackType,
    register_callback,
    unregister_callback,
)


def _load_provider():
    pkg_names = [
        "yosai_intel_dashboard",
        "yosai_intel_dashboard.src",
        "yosai_intel_dashboard.src.core",
        "yosai_intel_dashboard.src.services",
    ]
    for name in pkg_names:
        sys.modules.setdefault(name, types.ModuleType(name))
    proto_mod = types.ModuleType("yosai_intel_dashboard.src.core.interfaces.protocols")
    class EventBusProtocol:
        pass
    proto_mod.EventBusProtocol = EventBusProtocol
    sys.modules["yosai_intel_dashboard.src.core.interfaces.protocols"] = proto_mod
    analytics_mod = types.ModuleType("yosai_intel_dashboard.src.services.analytics_summary")
    analytics_mod.generate_sample_analytics = lambda: {"x": 1}
    sys.modules["yosai_intel_dashboard.src.services.analytics_summary"] = analytics_mod
    path = (
        Path(__file__).resolve().parents[1]
        / "yosai_intel_dashboard"
        / "src"
        / "services"
        / "websocket_data_provider.py"
    )
    spec = importlib.util.spec_from_file_location(
        "yosai_intel_dashboard.src.services.websocket_data_provider",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module.WebSocketDataProvider


def test_websocket_data_provider_publishes():
    Provider = _load_provider()
    events: list[dict] = []

    def handler(data):
        events.append(data)

    register_callback(CallbackType.ANALYTICS_UPDATE, handler, component_id="test")
    cfg = ConfigService({
        'metrics_interval': 0.01,
        'ping_interval': 0.01,
        'ping_timeout': 0.01,
    })
    provider = Provider(config=cfg)
    time.sleep(0.05)
    provider.stop()
    unregister_callback(CallbackType.ANALYTICS_UPDATE, handler)
    assert events
