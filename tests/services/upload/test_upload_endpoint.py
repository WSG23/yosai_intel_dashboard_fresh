from __future__ import annotations

import io
import types

import pytest
from flask import Flask

import sys
import types

pydantic = types.ModuleType("pydantic")
pydantic.BaseModel = object
pydantic.ConfigDict = dict
pydantic.ValidationError = Exception
sys.modules["pydantic"] = pydantic

stub_rate = types.ModuleType("middleware.rate_limit")
stub_rate.RedisRateLimiter = lambda *a, **k: None
stub_rate.rate_limit = lambda *a, **k: (lambda f: f)
sys.modules.setdefault("middleware.rate_limit", stub_rate)

stub_dp = types.ModuleType("yosai_intel_dashboard.src.services.data_processing")
stub_dp.FileHandler = lambda: types.SimpleNamespace(
    validator=types.SimpleNamespace(
        validate_file_upload=lambda filename, data: types.SimpleNamespace(valid=True, issues=[])
    )
)
sys.modules.setdefault("yosai_intel_dashboard.src.services.data_processing", stub_dp)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.services.data_processing.file_handler", stub_dp
)

stub_shared = types.ModuleType("shared.errors.types")
stub_shared.ErrorCode = types.SimpleNamespace(INVALID_INPUT="INVALID_INPUT", INTERNAL="INTERNAL")
sys.modules.setdefault("shared.errors.types", stub_shared)

stub_yf_errors = types.ModuleType("yosai_framework.errors")
stub_yf_errors.CODE_TO_STATUS = {"INVALID_INPUT": 400, "INTERNAL": 500}
sys.modules.setdefault("yosai_framework.errors", stub_yf_errors)
sys.modules.setdefault("yosai_framework", types.ModuleType("yosai_framework"))
stub_redis = types.ModuleType("redis")
stub_redis.Redis = types.SimpleNamespace(from_url=lambda url: types.SimpleNamespace())
sys.modules["redis"] = stub_redis

from yosai_intel_dashboard.src.services.upload.upload_endpoint import create_upload_blueprint


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("flask_wtf.csrf.validate_csrf", lambda token: None)
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.services.upload.file_validator.FileValidator.MAX_FILE_SIZE",
        10,
    )
    handler = types.SimpleNamespace(
        validator=types.SimpleNamespace(
            validate_file_upload=lambda filename, data: types.SimpleNamespace(
                valid=True, issues=[]
            )
        )
    )
    bp = create_upload_blueprint(tmp_path, file_handler=handler)
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test"
    app.register_blueprint(bp)
    return app, tmp_path


def test_happy_path(app):
    app_obj, storage = app
    client = app_obj.test_client()
    data = {"file": (io.BytesIO(b"a"), "good.csv", "text/csv")}
    resp = client.post("/api/v1/upload", data=data, headers={"X-CSRFToken": "x"})
    assert resp.status_code == 200
    assert resp.get_json()["results"][0]["filename"] == "good.csv"
    assert (storage / "good.csv").exists()


def test_bad_extension(app):
    app_obj, _ = app
    client = app_obj.test_client()
    data = {"file": (io.BytesIO(b"a"), "bad.exe", "application/octet-stream")}
    resp = client.post("/api/v1/upload", data=data, headers={"X-CSRFToken": "x"})
    assert resp.status_code == 400


def test_bad_mime(app):
    app_obj, _ = app
    client = app_obj.test_client()
    data = {"file": (io.BytesIO(b"a"), "good.csv", "application/json")}
    resp = client.post("/api/v1/upload", data=data, headers={"X-CSRFToken": "x"})
    assert resp.status_code == 400


def test_oversize_file(app):
    app_obj, _ = app
    client = app_obj.test_client()
    big = io.BytesIO(b"a" * 20)
    data = {"file": (big, "big.csv", "text/csv")}
    resp = client.post("/api/v1/upload", data=data, headers={"X-CSRFToken": "x"})
    assert resp.status_code == 400


def test_missing_file_field(app):
    app_obj, _ = app
    client = app_obj.test_client()
    resp = client.post("/api/v1/upload", headers={"X-CSRFToken": "x"})
    assert resp.status_code == 400


def test_multiple_files(app):
    app_obj, storage = app
    client = app_obj.test_client()
    data = {
        "f1": (io.BytesIO(b"a"), "a.csv", "text/csv"),
        "f2": (io.BytesIO(b"b"), "b.csv", "text/csv"),
    }
    resp = client.post("/api/v1/upload", data=data, headers={"X-CSRFToken": "x"})
    assert resp.status_code == 200
    assert (storage / "a.csv").exists()
    assert (storage / "b.csv").exists()
