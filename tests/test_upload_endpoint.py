import io
import base64
import importlib
import sys
import types
from pathlib import Path

from flask import Flask

from yosai_intel_dashboard.src.core.imports.resolver import safe_import
from yosai_intel_dashboard.src.error_handling import ErrorHandler


# Ensure package can be imported without installing as distribution
safe_import("yosai_intel_dashboard", types.ModuleType("yosai_intel_dashboard"))
sys.modules["yosai_intel_dashboard"].__path__ = [
    str(Path(__file__).resolve().parents[1] / "yosai_intel_dashboard")
]


def _create_app(tmp_path, handler: object | None = None):
    upload_ep = importlib.import_module(
        "yosai_intel_dashboard.src.services.upload_endpoint"
    )
    app = Flask(__name__)
    bp = upload_ep.create_upload_blueprint(
        storage_dir=tmp_path, file_handler=handler, handler=ErrorHandler()
    )
    app.register_blueprint(bp)
    return app


def test_upload_saves_file(tmp_path):
    app = _create_app(tmp_path)
    content_bytes = b"a\n1\n"
    b64 = base64.b64encode(content_bytes).decode()
    data_url = f"data:text/csv;base64,{b64}"
    client = app.test_client()
    resp = client.post(
        "/v1/upload", json={"contents": [data_url], "filenames": ["test.csv"]}
    )
    assert resp.status_code == 200
    assert (tmp_path / "test.csv").exists()
    body = resp.get_json()
    assert body["results"][0]["filename"] == "test.csv"


class TinyHandler:
    class Validator:
        def validate_file_upload(self, filename, data):
            class Res:
                def __init__(self):
                    self.valid = len(data) <= 0
                    self.issues = ["file_too_large"] if data else []

            return Res()

    def __init__(self):
        self.validator = self.Validator()


def test_upload_rejects_oversized_file(tmp_path):
    app = _create_app(tmp_path, TinyHandler())
    client = app.test_client()
    data = {"file": (io.BytesIO(b"123456"), "big.csv")}
    resp = client.post("/v1/upload", data=data)
    assert resp.status_code == 400


def test_upload_rejects_unsupported_file(tmp_path):
    app = _create_app(tmp_path)
    client = app.test_client()
    data = {"file": (io.BytesIO(b"abc"), "bad.exe")}
    resp = client.post("/v1/upload", data=data)
    assert resp.status_code == 400


def test_upload_rejects_path_traversal_filename(tmp_path):
    app = _create_app(tmp_path)
    client = app.test_client()
    content = "data:text/csv;base64,YSx6"
    resp = client.post(
        "/v1/upload", json={"contents": [content], "filenames": ["../bad.csv"]}
    )
    assert resp.status_code == 400

