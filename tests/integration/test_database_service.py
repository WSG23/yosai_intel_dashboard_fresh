import sys
import types
from types import SimpleNamespace
from pathlib import Path
import importlib.util

import tests.config  # noqa: F401 ensures environment setup

# Extend prometheus_client stub with Gauge and Histogram if missing
prom = sys.modules.get("prometheus_client")
if not prom:
    prom = types.ModuleType("prometheus_client")
    sys.modules["prometheus_client"] = prom

class _Metric:
    def __init__(self, *a, **k):
        pass

    def inc(self, *a, **k):
        pass

    def observe(self, *a, **k):
        pass

    def set(self, *a, **k):
        pass

if not hasattr(prom, "Gauge"):
    prom.Gauge = _Metric
if not hasattr(prom, "Histogram"):
    prom.Histogram = _Metric
if not hasattr(prom, "Counter"):
    prom.Counter = _Metric
if not hasattr(prom, "REGISTRY"):
    prom.REGISTRY = types.SimpleNamespace(_names_to_collectors={})

core = sys.modules.get("prometheus_client.core")
if not core:
    core = types.ModuleType("prometheus_client.core")
    sys.modules["prometheus_client.core"] = core
if not hasattr(core, "CollectorRegistry"):
    class CollectorRegistry:
        def __init__(self):
            self._names_to_collectors = {}
    core.CollectorRegistry = CollectorRegistry

# Stub sqlalchemy to satisfy optional imports
if "sqlalchemy" not in sys.modules:
    sqlalchemy = types.ModuleType("sqlalchemy")
    sqlalchemy.ext = types.SimpleNamespace(
        asyncio=types.SimpleNamespace(
            AsyncEngine=object, create_async_engine=lambda *a, **k: None
        )
    )
    sys.modules["sqlalchemy"] = sqlalchemy
    sys.modules["sqlalchemy.ext"] = sqlalchemy.ext
    sys.modules["sqlalchemy.ext.asyncio"] = sqlalchemy.ext.asyncio

# Provide lightweight core.unicode module
unicode_stub = types.ModuleType("yosai_intel_dashboard.src.core.unicode")
unicode_stub.safe_encode_text = lambda x: x
unicode_stub.sanitize_for_utf8 = lambda x: x
unicode_stub.safe_unicode_decode = lambda x: x
unicode_stub.clean_surrogate_chars = lambda x, replacement="": x
sys.modules["yosai_intel_dashboard.src.core.unicode"] = unicode_stub

# Avoid heavy utils package initialization
root = Path(__file__).resolve().parents[2]
utils_pkg = types.ModuleType("yosai_intel_dashboard.src.utils")
utils_pkg.__path__ = [str(root / "yosai_intel_dashboard" / "src" / "utils")]
sys.modules["yosai_intel_dashboard.src.utils"] = utils_pkg

# Stub plugin packages to bypass plugin initialization
plugins_pkg = types.ModuleType("yosai_intel_dashboard.src.core.plugins")
plugins_pkg.__path__ = [str(root / "yosai_intel_dashboard" / "src" / "core" / "plugins")]
config_pkg = types.ModuleType("yosai_intel_dashboard.src.core.plugins.config")
config_pkg.__path__ = [str(root / "yosai_intel_dashboard" / "src" / "core" / "plugins" / "config")]
sys.modules["yosai_intel_dashboard.src.core.plugins"] = plugins_pkg
sys.modules["yosai_intel_dashboard.src.core.plugins.config"] = config_pkg

from yosai_intel_dashboard.src.core.plugins.config.factories import DatabaseManagerFactory

# Load DatabaseAnalyticsService directly to avoid package side effects
service_path = root / "yosai_intel_dashboard" / "src" / "services" / "analytics" / "database_analytics_service.py"
spec = importlib.util.spec_from_file_location("database_analytics_service", service_path)
service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service_module)
DatabaseAnalyticsService = service_module.DatabaseAnalyticsService


class _ManagerAdapter:
    """Adapter providing the interface expected by DatabaseAnalyticsService."""

    def __init__(self, manager):
        self._manager = manager

    def get_connection(self):
        result = self._manager.get_connection()
        if not result.success:
            raise RuntimeError(result.error_message or "connection failed")
        return result.connection

    def release_connection(self, _connection):
        # SQLite manager maintains a single connection; nothing to release.
        pass

    def health_check(self) -> bool:
        return self._manager.test_connection()

    def close(self) -> None:
        self._manager.close_connection()


def test_database_service_integration():
    config = SimpleNamespace(type="sqlite", name=":memory:")
    raw_manager = DatabaseManagerFactory.create_manager(config)
    manager = _ManagerAdapter(raw_manager)

    try:
        assert manager.health_check()
        service = DatabaseAnalyticsService(manager)
        result = service.get_analytics()
        assert result["status"] in {"success", "error"}
        if result["status"] == "error":
            assert "message" in result
    finally:
        manager.close()
