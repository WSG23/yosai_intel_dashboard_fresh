import base64
import io
import importlib
import sys
import types
import zipfile
from pathlib import Path

import pytest
from flask import Flask

from yosai_intel_dashboard.src.error_handling import ErrorHandler
from yosai_intel_dashboard.src.core.imports.resolver import safe_import
from validation.security_validator import SecurityValidator


# Ensure package can be imported without installing as distribution
safe_import("yosai_intel_dashboard", types.ModuleType("yosai_intel_dashboard"))
sys.modules["yosai_intel_dashboard"].__path__ = [
    str(Path(__file__).resolve().parents[2] / "yosai_intel_dashboard")
]


def _create_app(tmp_path, handler: object | None = None):
    upload_ep = importlib.import_module(
        "yosai_intel_dashboard.src.services.upload.upload_endpoint"
    )
    app = Flask(__name__)
    bp = upload_ep.create_upload_blueprint(
        storage_dir=tmp_path, file_handler=handler, handler=ErrorHandler()
    )
    app.register_blueprint(bp)
    return app


class StrictHandler:
    class Validator(SecurityValidator):
        def validate_file_upload(self, filename, data):
            return self.validate_file_meta(filename, data)

    def __init__(self):
        self.validator = self.Validator()


def _csv_data_url(data: bytes, mime: str = "text/csv") -> str:
    b64 = base64.b64encode(data).decode()
    return f"data:{mime};base64,{b64}"


def test_path_traversal_rejected(tmp_path):
    app = _create_app(tmp_path)
    client = app.test_client()
    content = _csv_data_url(b"a,b")
    resp = client.post(
        "/v1/upload",
        json={"contents": [content], "filenames": ["../evil.csv"]},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["message"] == "Invalid filename"


def test_double_extension_rejected(tmp_path):
    app = _create_app(tmp_path, StrictHandler())
    client = app.test_client()
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
    content = _csv_data_url(png_bytes)
    resp = client.post(
        "/v1/upload",
        json={"contents": [content], "filenames": ["shell.php.csv"]},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert "file_signature_mismatch" in body["message"]


def test_null_byte_filename_rejected(tmp_path):
    app = _create_app(tmp_path)
    client = app.test_client()
    content = _csv_data_url(b"a,b")
    bad_name = "null.csv\x00.txt"
    resp = client.post(
        "/v1/upload",
        json={"contents": [content], "filenames": [bad_name]},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert "invalid_extension" in body["message"]


def test_mime_mismatch_rejected(tmp_path):
    app = _create_app(tmp_path)
    client = app.test_client()
    content = _csv_data_url(b"a,b", mime="text/plain")
    resp = client.post(
        "/v1/upload",
        json={"contents": [content], "filenames": ["test.csv"]},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["message"] == "Unsupported file type"


def test_oversize_file_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "1")
    app = _create_app(tmp_path)
    client = app.test_client()
    big = b"a" * (1024 * 1024 + 1)
    resp = client.post(
        "/v1/upload",
        data={"file": (io.BytesIO(big), "big.csv")},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["message"] == "File too large"


def test_zip_bomb_simulation_rejected(tmp_path):
    app = _create_app(tmp_path, StrictHandler())
    client = app.test_client()
    data = b"A" * (1024 * 1024)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data.txt", data)
    zip_bytes = buf.getvalue()
    content = _csv_data_url(zip_bytes)
    resp = client.post(
        "/v1/upload",
        json={"contents": [content], "filenames": ["bomb.csv"]},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert "file_signature_mismatch" in body["message"]
