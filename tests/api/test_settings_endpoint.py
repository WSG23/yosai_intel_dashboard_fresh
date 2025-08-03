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
    sys.modules["yosai_framework"] = fake_pkg
    sys.modules["yosai_framework.errors"] = fake_errors

    # Load utils.pydantic_decorators without importing utils package
    from flask import request
    pyd_module = ModuleType("pydantic_decorators")

    def _validate_input(model):
        def decorator(func):
            def wrapper(*args, **kwargs):
                data = request.get_json() or {}
                kwargs["payload"] = model.model_validate(data)
                return func(*args, **kwargs)
            return wrapper
        return decorator

    pyd_module.validate_input = _validate_input
    pyd_module.validate_output = lambda model: (lambda f: f)
    sys.modules["yosai_intel_dashboard.src.utils.pydantic_decorators"] = pyd_module

    error_module = ModuleType("error_handling")
    class _ErrorHandler:
        def handle(self, exc, category):
            return exc
    error_module.ErrorHandler = _ErrorHandler
    error_module.ErrorCategory = SimpleNamespace(INTERNAL="internal")
    error_module.api_error_response = lambda exc, category, handler=None: ({"error": str(exc)}, 500)
    sys.modules["yosai_intel_dashboard.src.error_handling"] = error_module

    settings_endpoint = importlib.import_module("api.settings_endpoint")

    monkeypatch.setattr(
        settings_endpoint, "SETTINGS_FILE", Path("settings.json"), raising=False
    )
    monkeypatch.setattr(
        settings_endpoint, "LOCK_FILE", Path("settings.json.lock"), raising=False
    )
    monkeypatch.setattr(settings_endpoint, "FileLock", lambda p: DummyLock())

    orig_exists = Path.exists
    orig_mkdir = Path.mkdir
    orig_open = Path.open

    def fake_exists(self: Path):
        if str(self) in fs:
            return True
        return orig_exists(self)

    def fake_mkdir(self: Path, parents: bool = False, exist_ok: bool = False):
        if str(self) in {str(settings_endpoint.SETTINGS_FILE.parent)}:
            return None
        return orig_mkdir(self, parents=parents, exist_ok=exist_ok)

    class FakeFile(io.StringIO):
        def __init__(self, path: str, mode: str):
            content = fs.get(path, "") if "r" in mode else ""
            super().__init__(content)
            self._path = path
            self._mode = mode

        def close(self):
            if "w" in self._mode or "a" in self._mode:
                fs[self._path] = self.getvalue()
            super().close()

    def fake_open(self: Path, mode: str = "r", encoding: str | None = None, errors: str | None = None, **kwargs):
        if str(self) in {str(settings_endpoint.SETTINGS_FILE), str(settings_endpoint.LOCK_FILE)}:
            return FakeFile(str(self), mode)
        return orig_open(self, mode, encoding=encoding, errors=errors, **kwargs)

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(Path, "mkdir", fake_mkdir)
    monkeypatch.setattr(Path, "open", fake_open)

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
