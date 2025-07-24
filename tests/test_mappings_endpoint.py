import pandas as pd
from flask import Flask

import os
import types
import sys
import importlib
from pathlib import Path

os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")
core_container_stub = types.ModuleType("core.container")
core_container_stub.container = types.SimpleNamespace(has=lambda n: False, get=lambda n: None)
sys.modules.setdefault("core.container", core_container_stub)
services_mod = sys.modules.setdefault("services", types.ModuleType("services"))
services_mod.__path__ = [str(Path(__file__).resolve().parents[1] / "services")]

# Provide stubs before importing the endpoint
if "dash" not in sys.modules:
    dash_stub = importlib.import_module("tests.stubs.dash")
    sys.modules["dash"] = dash_stub
    sys.modules["dash.dash"] = dash_stub
    sys.modules.setdefault("dash.html", dash_stub.html)
    sys.modules.setdefault("dash.dcc", dash_stub.dcc)
    sys.modules.setdefault("dash.dependencies", dash_stub.dependencies)
    sys.modules.setdefault("dash._callback", dash_stub._callback)

if "dash_bootstrap_components" not in sys.modules:
    dbc_stub = importlib.import_module("tests.stubs.dash_bootstrap_components")
    sys.modules["dash_bootstrap_components"] = dbc_stub

import mappings_endpoint
from core.service_container import ServiceContainer

# Provide stub for optional heavy dependencies
if "dask" not in sys.modules:
    dask_stub = types.ModuleType("dask")
    dask_stub.__path__ = []
    dist_stub = types.ModuleType("dask.distributed")
    dist_stub.Client = object
    dist_stub.LocalCluster = object
    sys.modules["dask"] = dask_stub
    sys.modules["dask.distributed"] = dist_stub


class DummyUploadProcessor:
    def __init__(self, store):
        self.store = store
from tests.fakes import FakeUploadStore


class StoreWithSave(FakeUploadStore):
    def store_data(self, filename: str, df: pd.DataFrame) -> None:
        self.add_file(filename, df)
from tests.fakes import FakeDeviceLearningService


class DummyColumnService:
    def __init__(self) -> None:
        self.saved: dict[str, dict[str, str]] = {}

    def save_column_mappings(self, filename: str, mapping: dict[str, str]) -> bool:
        self.saved[filename] = mapping
        return True


class DummyDeviceLearningService(FakeDeviceLearningService):
    def save_user_device_mapping(
        self,
        *,
        filename: str,
        device_name: str,
        device_type: str,
        location: str | None = None,
        properties: dict | None = None,
    ) -> bool:
        props = properties or {}
        if filename not in self.saved:
            self.saved[filename] = {}
        self.saved[filename][device_name] = {
            "device_type": device_type,
            "location": location,
            "properties": props,
        }
        return True


def _create_app(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(mappings_endpoint.mappings_bp)

    store = StoreWithSave()
    device_service = DummyDeviceLearningService()
    column_service = DummyColumnService()
    upload_processor = DummyUploadProcessor(store)

    container = ServiceContainer()
    container.register_singleton("upload_processor", upload_processor)
    container.register_singleton("device_learning_service", device_service)
    container.register_singleton("consolidated_learning_service", column_service)

    import core.service_container as sc
    monkeypatch.setattr(sc, "ServiceContainer", lambda: container)
    import core.container as cc
    monkeypatch.setattr(cc, "container", container)
    import services.mappings as sm
    monkeypatch.setattr(sm, "container", container)
    monkeypatch.setattr(mappings_endpoint, "container", container)

    return app, store, device_service, column_service


def test_save_mappings(monkeypatch):
    app, _store, device_service, column_service = _create_app(monkeypatch)
    client = app.test_client()

    resp = client.post(
        "/v1/mappings/save",
        json={
            "filename": "file.csv",
            "mapping_type": "column",
            "column_mappings": {"orig": "device_name"},
        },
    )
    assert resp.status_code == 200
    assert column_service.saved["file.csv"] == {"orig": "device_name"}

    resp = client.post(
        "/v1/mappings/save",
        json={
            "filename": "file.csv",
            "mapping_type": "device",
            "device_mappings": {
                "door1": {"device_type": "door", "location": "L1", "properties": {}}
            },
        },
    )
    assert resp.status_code == 200
    assert device_service.saved["file.csv"]["door1"]["device_type"] == "door"


def test_process_enhanced(monkeypatch):
    app, store, _device_service, _column_service = _create_app(monkeypatch)
    client = app.test_client()

    df = pd.DataFrame({"device_name": ["door1"], "val": [1]})
    store.add_file("file.csv", df)

    resp = client.post(
        "/v1/process-enhanced",
        json={
            "filename": "file.csv",
            "column_mappings": {"val": "value"},
            "device_mappings": {"door1": {"device_type": "door"}},
        },
    )
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert data["enhanced_filename"] == "enhanced_file.csv"
    assert "enhanced_file.csv" in store.get_filenames()
