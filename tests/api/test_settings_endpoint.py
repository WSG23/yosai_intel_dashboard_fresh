import importlib
import importlib.util
import io
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

from flask import Flask
from tests.import_helpers import safe_import, import_optional


class DummyLock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


def test_get_and_update_settings(monkeypatch):
    fs: dict[str, str] = {}

    # Stub flask_apispec before importing the endpoint
    monkeypatch.setitem(
        sys.modules, "flask_apispec", SimpleNamespace(doc=lambda *a, **k: (lambda f: f))
    )

    # Provide minimal yosai_framework.errors to avoid heavy deps
    fake_errors = ModuleType("yosai_framework.errors")
    from shared.errors.types import ErrorCode

    fake_errors.CODE_TO_STATUS = {
        ErrorCode.INVALID_INPUT: 400,
        ErrorCode.UNAUTHORIZED: 401,
        ErrorCode.NOT_FOUND: 404,
        ErrorCode.INTERNAL: 500,
        ErrorCode.UNAVAILABLE: 503,
    }
    fake_pkg = ModuleType("yosai_framework")
    fake_pkg.errors = fake_errors
    safe_import('yosai_framework', fake_pkg)
    safe_import('yosai_framework.errors', fake_errors)

    # Load utils.pydantic_decorators without importing utils package
    spec = importlib.util.spec_from_file_location(
        "utils.pydantic_decorators",
        Path(__file__).resolve().parents[2] / "utils" / "pydantic_decorators.py",
    )
    pyd_module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(pyd_module)
    utils_pkg = ModuleType("utils")
    utils_pkg.pydantic_decorators = pyd_module
    safe_import('utils', utils_pkg)
    safe_import('utils.pydantic_decorators', pyd_module)

    settings_endpoint = importlib.import_module("api.settings_endpoint")

    monkeypatch.setattr(
        settings_endpoint, "SETTINGS_FILE", "settings.json", raising=False
    )
    monkeypatch.setattr(
        settings_endpoint, "LOCK_FILE", "settings.json.lock", raising=False
    )
    monkeypatch.setattr(settings_endpoint, "FileLock", lambda p: DummyLock())

    def fake_exists(path):
        return path in fs

    def fake_makedirs(path, exist_ok=False):
        pass

    class FakeFile(io.StringIO):
        def __init__(self, path, mode):
            content = fs.get(path, "") if "r" in mode else ""
            super().__init__(content)
            self._path = path
            self._mode = mode

        def close(self):
            if "w" in self._mode or "a" in self._mode:
                fs[self._path] = self.getvalue()
            super().close()

    def fake_open(path, mode="r", encoding=None):
        return FakeFile(path, mode)

    monkeypatch.setattr(settings_endpoint.os.path, "exists", fake_exists)
    monkeypatch.setattr(settings_endpoint.os, "makedirs", fake_makedirs)
    monkeypatch.setattr("builtins.open", fake_open)

    app = Flask(__name__)
    app.register_blueprint(settings_endpoint.settings_bp)
    client = app.test_client()

    resp = client.get("/v1/settings")
    assert resp.status_code == 200
    assert resp.get_json() == settings_endpoint.DEFAULT_SETTINGS

    payload = {"theme": "dark", "itemsPerPage": 20}
    resp = client.post("/v1/settings", json=payload)
    assert resp.status_code == 200
    assert json.loads(fs["settings.json"]) == payload

    resp = client.get("/v1/settings")
    assert resp.status_code == 200
    assert resp.get_json() == payload
