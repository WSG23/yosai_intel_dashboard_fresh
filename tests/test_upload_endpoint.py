import asyncio
import importlib
import io
import sys
import types

import pandas as pd
from flask import Flask

from core.service_container import ServiceContainer
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder


class DummyStore:
    def get_all_data(self):
        return {}


class DummyUploadService:
    def __init__(self):
        self.store = DummyStore()
        self.called_args = None

    async def process_uploaded_files(self, contents, filenames):
        self.called_args = (contents, filenames)
        return {
            "upload_results": [],
            "file_preview_components": [],
            "file_info_dict": {},
        }


def _create_app(monkeypatch):
    # Provide minimal stubs to avoid heavy imports during module load
    fake_reg = types.ModuleType("services.upload.service_registration")
    fake_reg.register_upload_services = lambda c: c.register_singleton(
        "uploader", object()
    )
    monkeypatch.setitem(sys.modules, "services.upload.service_registration", fake_reg)

    cont = ServiceContainer()
    service = DummyUploadService()
    cont.register_singleton("upload_processor", service)

    container_mod = types.ModuleType("core.container")
    container_mod.container = cont
    monkeypatch.setitem(sys.modules, "core.container", container_mod)

    upload_ep = importlib.import_module("services.upload_endpoint")

    app = Flask(__name__)
    app.register_blueprint(upload_ep.upload_bp)
    monkeypatch.setattr(upload_ep, "container", cont, raising=False)
    return app, service


def test_upload_files_uses_asyncio_run(monkeypatch):
    app, service = _create_app(monkeypatch)

    used = {}
    orig_run = asyncio.run

    def fake_run(coro):
        used["called"] = True
        return orig_run(coro)

    monkeypatch.setattr(asyncio, "run", fake_run)

    df = DataFrameBuilder().add_column("a", [1]).build()
    content = UploadFileBuilder().with_dataframe(df).as_base64()
    client = app.test_client()
    resp = client.post(
        "/v1/upload",
        json={"contents": [content], "filenames": ["test.csv"]},
    )
    assert resp.status_code == 200
    assert used.get("called") is True
    assert service.called_args == ([content], ["test.csv"])


class FailingUploadService:
    def __init__(self):
        self.store = DummyStore()

    async def process_uploaded_files(self, contents, filenames):
        raise RuntimeError("boom")


def test_upload_returns_error_on_exception(monkeypatch):
    fake_reg = types.ModuleType("services.upload.service_registration")
    fake_reg.register_upload_services = lambda c: c.register_singleton(
        "uploader", object()
    )
    monkeypatch.setitem(sys.modules, "services.upload.service_registration", fake_reg)

    cont = ServiceContainer()
    service = FailingUploadService()
    cont.register_singleton("upload_processor", service)

    container_mod = types.ModuleType("core.container")
    container_mod.container = cont
    monkeypatch.setitem(sys.modules, "core.container", container_mod)

    import importlib

    upload_ep = importlib.import_module("services.upload_endpoint")

    app = Flask(__name__)
    app.register_blueprint(upload_ep.upload_bp)
    monkeypatch.setattr(upload_ep, "container", cont, raising=False)

    client = app.test_client()
    resp = client.post(
        "/v1/upload",
        json={"contents": ["data:text/csv;base64,YSx6"], "filenames": ["t.csv"]},
    )
    assert resp.status_code == 500
    body = resp.get_json()
    assert body == {"code": "internal", "message": "boom"}


class DummyValidator:
    def validate_file_upload(self, filename, content):
        if filename.endswith(".exe"):
            raise ValueError("unsupported")
        if len(content) > 5:
            raise ValueError("too_large")


class DummyFileProcessor:
    def __init__(self):
        self.validator = DummyValidator()

    def process_file_async(self, contents, filename):
        return "job123"

    def get_job_status(self, job_id):
        return {}


def _create_validator_app(monkeypatch):
    fake_reg = types.ModuleType("services.upload.service_registration")
    fake_reg.register_upload_services = lambda c: c.register_singleton(
        "uploader", object()
    )
    monkeypatch.setitem(sys.modules, "services.upload.service_registration", fake_reg)

    cont = ServiceContainer()
    cont.register_singleton("file_processor", DummyFileProcessor())

    container_mod = types.ModuleType("core.container")
    container_mod.container = cont
    monkeypatch.setitem(sys.modules, "core.container", container_mod)

    upload_ep = importlib.import_module("services.upload_endpoint")

    app = Flask(__name__)
    app.register_blueprint(upload_ep.upload_bp)
    monkeypatch.setattr(upload_ep, "container", cont, raising=False)
    return app


def test_upload_rejects_oversized_file(monkeypatch):
    app = _create_validator_app(monkeypatch)
    client = app.test_client()
    data = {"file": (io.BytesIO(b"123456"), "big.csv")}
    resp = client.post("/v1/upload", data=data)
    assert resp.status_code == 400


def test_upload_rejects_unsupported_file(monkeypatch):
    app = _create_validator_app(monkeypatch)
    client = app.test_client()
    data = {"file": (io.BytesIO(b"abc"), "bad.exe")}
    resp = client.post("/v1/upload", data=data)
    assert resp.status_code == 400
