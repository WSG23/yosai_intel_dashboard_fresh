import importlib
import os
import sys
from pathlib import Path
import types
from tests.import_helpers import safe_import, import_optional

# Provide stubs when optional dependencies are missing
if "flask_wtf" not in sys.modules:
    fw = importlib.import_module("tests.stubs.flask_wtf")
    safe_import('flask_wtf', fw)
    safe_import('flask_wtf.csrf', fw)
if "flask_caching" not in sys.modules:
    safe_import('flask_caching', importlib.import_module("tests.stubs.flask_caching"))
if "flask_cors" not in sys.modules:
    safe_import('flask_cors', importlib.import_module("tests.stubs.flask_cors"))
if "services" not in sys.modules:
    safe_import('services', importlib.import_module("tests.stubs.services"))

safe_import('yosai_intel_dashboard', types.ModuleType("yosai_intel_dashboard"))
sys.modules["yosai_intel_dashboard"].__path__ = [str(Path(__file__).resolve().parents[1] / "yosai_intel_dashboard")]

import werkzeug
from flask import Flask, jsonify

from yosai_intel_dashboard.src.error_handling import ErrorHandler
from tests.stubs.flask_wtf import CSRFProtect, generate_csrf


class DummyUploadService:
    async def process_uploaded_files(self, contents, filenames):
        return {
            "upload_results": [],
            "file_preview_components": [],
            "file_info_dict": {},
        }


def _create_app(monkeypatch):
    from yosai_intel_dashboard.src.services import upload_endpoint

    app = Flask(__name__)
    # Use a throwaway value instead of a real secret
    app.config["SECRET_KEY"] = os.urandom(16).hex()
    CSRFProtect(app)
    if not hasattr(werkzeug, "__version__"):
        werkzeug.__version__ = "3"
    bp = upload_endpoint.create_upload_blueprint(DummyUploadService(), handler=ErrorHandler())
    app.register_blueprint(bp)

    @app.route("/v1/csrf-token")
    def csrf_token():
        return jsonify({"csrf_token": generate_csrf()})

    return app


def test_upload_requires_csrf(monkeypatch):
    app = _create_app(monkeypatch)
    client = app.test_client()

    resp = client.post("/v1/upload", json={"contents": [], "filenames": []})
    assert resp.status_code == 400

    with client:
        token = client.get("/v1/csrf-token").get_json()["csrf_token"]
        resp = client.post(
            "/v1/upload",
            json={"contents": [], "filenames": []},
            headers={"X-CSRFToken": token},
        )
        assert resp.status_code == 200
