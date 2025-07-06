import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("container", ROOT / "core" / "container.py")
module = importlib.util.module_from_spec(spec)
sys.modules["container"] = module
spec.loader.exec_module(module)  # type: ignore
Container = module.Container


def test_container_initialization():
    container = Container()
    assert isinstance(container._services, dict)
    assert container._services == {}


def test_service_registration_and_retrieval():
    container = Container()
    service = Mock()
    container.register("svc", service)

    assert container.has("svc") is True
    assert container.get("svc") is service


def test_get_missing_service_returns_none():
    container = Container()
    assert container.get("missing") is None
    assert container.has("missing") is False
