from core.service_container import ServiceContainer
import types
import sys
import os
from pathlib import Path

os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")
services_mod = sys.modules.setdefault("services", types.ModuleType("services"))
services_mod.__path__ = [str(Path(__file__).resolve().parents[2] / "services")]
import services.mappings as mappings


def _setup(monkeypatch):
    container = ServiceContainer()
    monkeypatch.setattr(mappings, "container", container)
    config_pkg = types.ModuleType("config")
    sr_stub = types.ModuleType("config.service_registration")
    sr_stub.register_upload_services = lambda c: None
    config_pkg.service_registration = sr_stub
    monkeypatch.setitem(sys.modules, "config", config_pkg)
    monkeypatch.setitem(sys.modules, "config.service_registration", sr_stub)
    return container


class DummyColumnService:
    def __init__(self):
        self.calls = []

    def save_column_mappings(self, file_id: str, mapping: dict[str, str]) -> None:
        self.calls.append((file_id, mapping))


class DummyDeviceService:
    def __init__(self):
        self.calls = []

    def save_user_device_mapping(self, *, filename: str, device_name: str, device_type: str, location=None, properties=None):
        self.calls.append((filename, device_name, device_type, location, properties or {}))


def test_save_column_mappings(monkeypatch):
    container = _setup(monkeypatch)
    svc = DummyColumnService()
    container.register_singleton("consolidated_learning_service", svc)

    mappings.save_column_mappings("file.csv", {"a": "b"})

    assert svc.calls == [("file.csv", {"a": "b"})]


def test_save_device_mappings(monkeypatch):
    container = _setup(monkeypatch)
    svc = DummyDeviceService()
    container.register_singleton("device_learning_service", svc)

    mappings.save_device_mappings(
        "file.csv",
        {"door1": {"device_type": "door", "location": "L1"}},
    )

    assert svc.calls == [
        ("file.csv", "door1", "door", "L1", {}),
    ]

