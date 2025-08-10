from __future__ import annotations

import io
import types
import sys

import pytest
from flask import Flask

import pydantic
sys.modules["pydantic"] = pydantic

from yosai_intel_dashboard.src.infrastructure.validation.file_validator import (
    FileValidator,
)
from yosai_intel_dashboard.src.services.upload_endpoint import create_upload_blueprint


class StubProcessor:
    def __init__(self):
        self.validator = FileValidator(max_size_mb=1, allowed_ext=[".csv"])
        self.called = None

    def process_file_async(self, content, filename):
        self.called = (content, filename)
        return "job-1"

    def get_job_status(self, job_id):
        return {"status": {"done": True}}


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setattr("redis.Redis.from_url", lambda url: types.SimpleNamespace())
    monkeypatch.setattr(
        "middleware.rate_limit.rate_limit", lambda *a, **k: (lambda f: f)
    )
    monkeypatch.setattr("flask_wtf.csrf.validate_csrf", lambda token: None)
    processor = StubProcessor()
    bp = create_upload_blueprint(processor, handler=None)
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test"
    app.register_blueprint(bp)
    return app, processor


def test_happy_path(app):
    app_obj, processor = app
    client = app_obj.test_client()
    data = {"file": (io.BytesIO(b"a,b\n1,2"), "good.csv")}
    resp = client.post("/v1/upload", data=data, headers={"X-CSRFToken": "x"})
    assert resp.status_code == 202
    assert resp.get_json() == {"job_id": "job-1"}
    assert processor.called[1] == "good.csv"


def test_bad_extension(app):
    app_obj, _ = app
    client = app_obj.test_client()
    data = {"file": (io.BytesIO(b"abc"), "bad.exe")}
    resp = client.post("/v1/upload", data=data, headers={"X-CSRFToken": "x"})
    assert resp.status_code == 400


def test_oversize_file(app):
    app_obj, _ = app
    client = app_obj.test_client()
    big = io.BytesIO(b"a" * (2 * 1024 * 1024))
    data = {"file": (big, "big.csv")}
    resp = client.post("/v1/upload", data=data, headers={"X-CSRFToken": "x"})
    assert resp.status_code == 400


def test_missing_file_field(app):
    app_obj, _ = app
    client = app_obj.test_client()
    resp = client.post("/v1/upload", headers={"X-CSRFToken": "x"})
    assert resp.status_code == 400


def test_multiple_files(app):
    app_obj, processor = app
    client = app_obj.test_client()
    data = {
        "f1": (io.BytesIO(b"a"), "a.csv"),
        "f2": (io.BytesIO(b"b"), "b.csv"),
    }
    resp = client.post("/v1/upload", data=data, headers={"X-CSRFToken": "x"})
    assert resp.status_code == 202
    assert processor.called[1] == "a.csv"
