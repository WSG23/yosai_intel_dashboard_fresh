import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("container", ROOT / "core" / "container.py")
container_module = importlib.util.module_from_spec(spec)
sys.modules["container"] = container_module
spec.loader.exec_module(container_module)  # type: ignore
Container = container_module.Container

sys.path.append(str(ROOT))

sys.modules.setdefault("pandas", SimpleNamespace(DataFrame=object))

from config.config import ConfigManager
from services.analytics_service import AnalyticsService


def test_container_initializes_without_circular_dependencies():
    for var in [
        "SECRET_KEY",
        "DB_PASSWORD",
        "AUTH0_CLIENT_ID",
        "AUTH0_CLIENT_SECRET",
        "AUTH0_DOMAIN",
        "AUTH0_AUDIENCE",
    ]:
        os.environ.setdefault(var, "test")
    container = Container()
    cfg = ConfigManager()
    analytics = AnalyticsService()

    container.register("config", cfg)
    container.register("analytics", analytics)

    assert container.get("config") is cfg
    assert container.get("analytics") is analytics
