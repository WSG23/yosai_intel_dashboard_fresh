"""Test configuration and fixtures"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

_missing_packages = [
    pkg for pkg in ("yaml", "psutil") if importlib.util.find_spec(pkg) is None
]
if _missing_packages:
    missing = ", ".join(_missing_packages)
    raise RuntimeError(
        f"Missing required test dependencies: {missing}. "
        "Install them with `pip install -r requirements-test.txt`."
    )

# Provide a lightweight 'services' package to avoid importing heavy dependencies
if "services" not in sys.modules:
    services_stub = types.ModuleType("services")
    services_stub.__path__ = []
    sys.modules["services"] = services_stub

# Optional heavy dependencies used by a subset of tests
_optional_packages = {"hvac", "cryptography", "boto3", "confluent_kafka"}
_missing_optional = [
    pkg for pkg in _optional_packages if importlib.util.find_spec(pkg) is None
]

if "hvac" not in sys.modules and "hvac" in _missing_optional:
    hvac_stub = types.ModuleType("hvac")
    hvac_stub.Client = object
    sys.modules["hvac"] = hvac_stub

if "cryptography" not in sys.modules and "cryptography" in _missing_optional:
    crypto_stub = types.ModuleType("cryptography")
    fernet_stub = types.ModuleType("cryptography.fernet")

    class DummyFernet:
        def __init__(self, *args, **kwargs): ...

        @staticmethod
        def generate_key() -> bytes:
            return b""

        def encrypt(self, data: bytes) -> bytes:
            return data

        def decrypt(self, data: bytes) -> bytes:
            return data

    fernet_stub.Fernet = DummyFernet
    crypto_stub.fernet = fernet_stub
    sys.modules["cryptography"] = crypto_stub
    sys.modules["cryptography.fernet"] = fernet_stub

if "boto3" not in sys.modules and "boto3" in _missing_optional:
    sys.modules["boto3"] = types.ModuleType("boto3")

if "confluent_kafka" not in sys.modules and "confluent_kafka" in _missing_optional:
    sys.modules["confluent_kafka"] = types.ModuleType("confluent_kafka")

if "monitoring.prometheus" not in sys.modules:
    prom_pkg = types.ModuleType("monitoring.prometheus")
    prom_pkg.__path__ = []
    dep_mod = types.ModuleType("monitoring.prometheus.deprecation")
    dep_mod.deprecated_calls = []
    dep_mod.record_deprecated_call = lambda name: dep_mod.deprecated_calls.append(name)
    dep_mod.start_deprecation_metrics_server = lambda *a, **k: None
    metrics_mod = types.ModuleType("monitoring.prometheus.model_metrics")
    metrics_mod.update_model_metrics = lambda *a, **k: None
    sys.modules["monitoring.prometheus"] = prom_pkg
    sys.modules["monitoring.prometheus.deprecation"] = dep_mod
    sys.modules["monitoring.prometheus.model_metrics"] = metrics_mod


def pytest_ignore_collect(path, config):
    """Skip tests requiring optional packages when they are not installed."""

    if path.basename == "test_secure_config_manager.py" and _missing_optional:
        reason = ", ".join(_missing_optional)
        import warnings

        warnings.warn(
            f"Skipping secure config tests, missing: {reason}",
            category=pytest.PytestWarning,
            stacklevel=2,
        )
        return True
    return False


try:  # use real package if available
    import dash_bootstrap_components  # noqa: F401
except Exception:  # pragma: no cover - fallback stub
    import tests.stubs.dash_bootstrap_components as dbc_stub

    if "dash_bootstrap_components" not in sys.modules:
        sys.modules["dash_bootstrap_components"] = dbc_stub
    if not hasattr(dbc_stub, "themes"):
        dbc_stub.themes = types.SimpleNamespace(BOOTSTRAP="bootstrap")

try:  # use real Dash if available
    import dash  # noqa: F401
except Exception:  # pragma: no cover - fallback stub
    dash_stub = importlib.import_module("tests.stubs.dash")
    sys.modules.setdefault("dash", dash_stub)
    sys.modules.setdefault("dash.html", dash_stub.html)
    sys.modules.setdefault("dash.dcc", dash_stub.dcc)
    sys.modules.setdefault("dash.dependencies", dash_stub.dependencies)
    sys.modules.setdefault("dash._callback", dash_stub._callback)
    sys.modules.setdefault(
        "dash.exceptions",
        types.SimpleNamespace(PreventUpdate=Exception),
    )
    dash_stub.no_update = dash_stub._callback.NoUpdate()

try:  # use real redis if available
    import redis  # noqa: F401
except Exception:  # pragma: no cover - fallback stub
    redis_stub = importlib.import_module("tests.stubs.redis")
    sys.modules.setdefault("redis", redis_stub)
    sys.modules.setdefault("redis.asyncio", redis_stub.asyncio)


import asyncio
import shutil
import tempfile
from typing import Any, Generator

import pandas as pd
import pytest

from tests.fake_unicode_processor import FakeUnicodeProcessor

try:
    from services.upload.protocols import UploadStorageProtocol
except Exception:  # pragma: no cover - optional dep fallback
    from typing import Protocol

    class UploadStorageProtocol(Protocol):
        def add_file(self, filename: str, dataframe: pd.DataFrame) -> None: ...
        def get_all_data(self) -> dict[str, pd.DataFrame]: ...
        def clear_all(self) -> None: ...


try:
    from core.protocols import ConfigurationProtocol
except Exception:  # pragma: no cover - optional dep fallback

    class ConfigurationProtocol(Protocol):
        def get_database_config(self) -> dict[str, Any]: ...
        def get_app_config(self) -> dict[str, Any]: ...
        def get_security_config(self) -> dict[str, Any]: ...
        def get_upload_config(self) -> dict[str, Any]: ...
        def reload_config(self) -> None: ...
        def validate_config(self) -> dict[str, Any]: ...


from core.container import Container

try:  # Optional real models may not be available in minimal environments
    from models.entities import AccessEvent, Door, Person
    from models.enums import AccessResult, DoorType
except Exception:  # pragma: no cover - fallback stubs
    AccessEvent = Door = Person = object
    AccessResult = DoorType = object


@pytest.fixture
def stub_services_registry(monkeypatch: pytest.MonkeyPatch):
    """Provide a minimal ``services.registry`` stub."""

    services_mod = types.ModuleType("services")
    registry_mod = types.ModuleType("services.registry")
    registry_mod.get_service = lambda name: None
    services_mod.registry = registry_mod
    monkeypatch.setitem(sys.modules, "services", services_mod)
    monkeypatch.setitem(sys.modules, "services.registry", registry_mod)
    return registry_mod


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for tests"""

    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def di_container() -> Container:
    """Create DI container for tests"""

    return Container()


@pytest.fixture
def fake_unicode_processor() -> FakeUnicodeProcessor:
    """Provide a minimal UnicodeProcessor for DI usage."""

    return FakeUnicodeProcessor()


@pytest.fixture
def upload_data_service(tmp_path: Path):
    """Provide a fresh ``UploadDataService`` backed by a temp store."""

    from services.upload_data_service import UploadDataService
    from utils.upload_store import UploadedDataStore

    store = UploadedDataStore(storage_dir=tmp_path)
    service = UploadDataService(store)
    yield service


@pytest.fixture
def sample_access_data() -> pd.DataFrame:
    """Sample access data for testing"""

    return pd.DataFrame(
        [
            {
                "person_id": "EMP001",
                "door_id": "MAIN_ENTRANCE",
                "timestamp": "2024-01-15 09:00:00",
                "access_result": AccessResult.GRANTED.value,
            },
            {
                "person_id": "EMP002",
                "door_id": "SERVER_ROOM",
                "timestamp": "2024-01-15 23:00:00",
                "access_result": AccessResult.DENIED.value,
            },
        ]
    )


@pytest.fixture
def sample_persons() -> list[Person]:
    """Sample person entities for testing"""

    return [
        Person(
            person_id="EMP001",
            name="John Doe",
            department="IT",
            clearance_level=3,
        ),
        Person(
            person_id="EMP002",
            name="Jane Smith",
            department="Security",
            clearance_level=5,
        ),
    ]


@pytest.fixture
def sample_doors() -> list[Door]:
    """Sample door entities for testing"""

    return [
        Door(
            door_id="MAIN_ENTRANCE",
            door_name="Main Entrance",
            facility_id="HQ",
            area_id="LOBBY",
            door_type=DoorType.STANDARD,
        ),
        Door(
            door_id="SERVER_ROOM",
            door_name="Server Room",
            facility_id="HQ",
            area_id="IT_FLOOR",
            door_type=DoorType.CRITICAL,
            required_clearance=4,
        ),
    ]


@pytest.fixture(autouse=True)
def env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide default environment variables for tests."""
    required = {
        "SECRET_KEY": "test",
        "DB_PASSWORD": "pwd",
        "AUTH0_CLIENT_ID": "cid",
        "AUTH0_CLIENT_SECRET": "secret",
        "AUTH0_DOMAIN": "domain",
        "AUTH0_AUDIENCE": "aud",
    }
    for key, value in required.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setup required authentication environment variables"""
    auth_vars = {
        "AUTH0_CLIENT_ID": "test_client",
        "AUTH0_CLIENT_SECRET": "test_secret",
        "AUTH0_DOMAIN": "test.auth0.com",
        "AUTH0_AUDIENCE": "test_audience",
    }
    for key, value in auth_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def async_runner() -> Generator[callable, None, None]:
    """Run async coroutines in a dedicated event loop."""

    yield asyncio.run


@pytest.fixture
def fake_dash(monkeypatch: pytest.MonkeyPatch, request):
    """Provide a lightweight Dash substitute for tests."""

    dash_stub = importlib.import_module("tests.stubs.dash")
    monkeypatch.setitem(sys.modules, "dash", dash_stub)
    monkeypatch.setitem(sys.modules, "dash.html", dash_stub.html)
    monkeypatch.setitem(sys.modules, "dash.dcc", dash_stub.dcc)
    monkeypatch.setitem(sys.modules, "dash.dependencies", dash_stub.dependencies)
    monkeypatch.setitem(sys.modules, "dash._callback", dash_stub._callback)
    monkeypatch.setitem(
        sys.modules,
        "dash.exceptions",
        types.SimpleNamespace(PreventUpdate=Exception),
    )
    dash_stub.no_update = dash_stub._callback.NoUpdate()

    attrs = {
        "dash": dash_stub,
        "Dash": dash_stub.Dash,
        "dcc": dash_stub.dcc,
        "html": dash_stub.html,
        "Input": dash_stub.dependencies.Input,
        "Output": dash_stub.dependencies.Output,
        "State": dash_stub.dependencies.State,
        "no_update": dash_stub.no_update,
    }
    for name, val in attrs.items():
        if hasattr(request.module, name):
            monkeypatch.setattr(request.module, name, val, raising=False)

    for mod_name in (
        "components.column_verification",
        "components.device_verification",
        "components.simple_device_mapping",
    ):
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
            for name, val in attrs.items():
                if hasattr(mod, name):
                    monkeypatch.setattr(mod, name, val, raising=False)

    yield dash_stub


@pytest.fixture
def fake_dbc(monkeypatch: pytest.MonkeyPatch, request):
    """Provide a minimal dash_bootstrap_components substitute."""

    import tests.stubs.dash_bootstrap_components as dbc_stub

    if not hasattr(dbc_stub, "themes"):
        dbc_stub.themes = types.SimpleNamespace(BOOTSTRAP="bootstrap")

    monkeypatch.setitem(sys.modules, "dash_bootstrap_components", dbc_stub)
    if hasattr(request.module, "dbc"):
        monkeypatch.setattr(request.module, "dbc", dbc_stub, raising=False)
    for mod_name in (
        "components.column_verification",
        "components.device_verification",
    ):
        if mod_name in sys.modules:
            monkeypatch.setattr(sys.modules[mod_name], "dbc", dbc_stub, raising=False)

    yield dbc_stub


class FakeUploadStore:
    """Minimal in-memory upload store for tests."""

    def __init__(self) -> None:
        self.data: dict[str, pd.DataFrame] = {}

    def add_file(self, filename: str, dataframe: pd.DataFrame) -> None:
        self.data[filename] = dataframe

    def get_all_data(self) -> dict[str, pd.DataFrame]:
        return self.data.copy()

    def clear_all(self) -> None:
        self.data.clear()

    def load_dataframe(self, filename: str) -> pd.DataFrame | None:
        return self.data.get(filename)

    def get_filenames(self) -> list[str]:
        return list(self.data.keys())

    def get_file_info(self) -> dict[str, dict[str, Any]]:
        return {
            name: {"rows": len(df), "columns": len(df.columns)}
            for name, df in self.data.items()
        }

    def wait_for_pending_saves(self) -> None:  # pragma: no cover - sync store
        pass


@pytest.fixture
def fake_upload_storage() -> FakeUploadStore:
    """Provide a fresh in-memory upload store."""
    return FakeUploadStore()


@pytest.fixture
def query_recorder():
    """Wrap a database connection to record executed queries."""

    from tests.utils.query_recorder import QueryRecordingConnection

    def factory(connection: Any) -> QueryRecordingConnection:
        return QueryRecordingConnection(connection)

    return factory
