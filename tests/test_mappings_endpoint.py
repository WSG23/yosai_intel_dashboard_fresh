import importlib
import sys
import types
from pathlib import Path
from tests.import_helpers import safe_import, import_optional

safe_import('yosai_intel_dashboard', types.ModuleType("yosai_intel_dashboard"))
sys.modules["yosai_intel_dashboard"].__path__ = [str(Path(__file__).resolve().parents[1] / "yosai_intel_dashboard")]

import pandas as pd
from flask import Flask

core_root = Path(__file__).resolve().parents[1] / "core"
core_pkg = types.ModuleType("core")
core_pkg.__path__ = [str(core_root)]
safe_import('core', core_pkg)

spec = importlib.util.spec_from_file_location(
    "core.service_container",
    core_root / "service_container.py",
)
sc_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
safe_import('core.service_container', sc_module)
spec.loader.exec_module(sc_module)

container_mod = types.ModuleType("core.container")
container_mod.container = sc_module.ServiceContainer()
safe_import('core.container', container_mod)

spec_pd = importlib.util.spec_from_file_location(
    "utils.pydantic_decorators",
    Path(__file__).resolve().parents[1] / "utils" / "pydantic_decorators.py",
)
pyd_module = importlib.util.module_from_spec(spec_pd)
assert spec_pd.loader is not None
fake_errors = types.ModuleType("yosai_framework.errors")
from shared.errors.types import ErrorCode

fake_errors.CODE_TO_STATUS = {
    ErrorCode.INVALID_INPUT: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.INTERNAL: 500,
    ErrorCode.UNAVAILABLE: 503,
}
fake_pkg = types.ModuleType("yosai_framework")
fake_pkg.errors = fake_errors
safe_import('yosai_framework', fake_pkg)
safe_import('yosai_framework.errors', fake_errors)

safe_import('utils.pydantic_decorators', pyd_module)
spec_pd.loader.exec_module(pyd_module)
utils_pkg = types.ModuleType("utils")
utils_pkg.pydantic_decorators = pyd_module
safe_import('utils', utils_pkg)
safe_import('utils.pydantic_decorators', pyd_module)

service_reg_stub = types.ModuleType("services.upload.service_registration")
service_reg_stub.register_upload_services = lambda c: None
config_pkg = types.ModuleType("config")
config_pkg.__path__ = []


class DatabaseSettings:
    def __init__(self, type: str = "sqlite", **kwargs: object) -> None:
        self.type = type
        self.host = ""
        self.port = 0
        self.name = ":memory:"
        self.user = ""
        self.password = ""
        self.connection_timeout = 1


config_pkg.service_registration = service_reg_stub
config_pkg.DatabaseSettings = DatabaseSettings
config_pkg.dynamic_config = types.SimpleNamespace(
    performance=types.SimpleNamespace(memory_usage_threshold_mb=1024)
)
safe_import('config', config_pkg)
safe_import('services.upload.service_registration', service_reg_stub)
safe_import('config.dynamic_config', config_pkg)

if "flask_apispec" not in sys.modules:
    safe_import('flask_apispec', types.SimpleNamespace()
        doc=lambda *a, **k: (lambda f: f)
    )

from error_handling import ErrorHandler
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from yosai_intel_dashboard.src.services import mappings_endpoint

# Ensure dash stubs are available for service imports
if "dash" not in sys.modules:
    dash_stub = importlib.import_module("tests.stubs.dash")
    safe_import('dash', dash_stub)
    safe_import('dash.dash', dash_stub)
    safe_import('dash.html', dash_stub.html)
    safe_import('dash.dcc', dash_stub.dcc)
    safe_import('dash.dependencies', dash_stub.dependencies)
    safe_import('dash._callback', dash_stub._callback)

if "dash_bootstrap_components" not in sys.modules:
    dbc_stub = importlib.import_module("tests.stubs.dash_bootstrap_components")
    safe_import('dash_bootstrap_components', dbc_stub)

# Provide stub for optional heavy dependencies
if "dask" not in sys.modules:
    dask_stub = types.ModuleType("dask")
    dask_stub.__path__ = []
    dist_stub = types.ModuleType("dask.distributed")
    dist_stub.Client = object
    dist_stub.LocalCluster = object
    safe_import('dask', dask_stub)
    safe_import('dask.distributed', dist_stub)


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

    store = StoreWithSave()
    device_service = DummyDeviceLearningService()
    column_service = DummyColumnService()
    upload_processor = DummyUploadProcessor(store)

    bp = mappings_endpoint.create_mappings_blueprint(
        upload_processor,
        device_service,
        column_service,
        handler=ErrorHandler(),
    )
    app.register_blueprint(bp)

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
