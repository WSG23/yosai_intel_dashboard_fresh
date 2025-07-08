"""Test configuration and fixtures"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
# Ensure test stubs (e.g., a Dash stub) are available before real packages
stub_dir = Path(__file__).resolve().parent / "stubs"
sys.path.insert(0, str(stub_dir))

import shutil
import tempfile
from typing import Any, Generator

import pandas as pd
import pytest

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


class _FakeUploadStorage(UploadStorageProtocol):
    """In-memory implementation of :class:`UploadStorageProtocol`."""

    def __init__(self) -> None:
        self._data: dict[str, pd.DataFrame] = {}

    def add_file(self, filename: str, dataframe: pd.DataFrame) -> None:
        self._data[filename] = dataframe

    def get_all_data(self) -> dict[str, pd.DataFrame]:
        return {name: df.copy() for name, df in self._data.items()}

    def clear_all(self) -> None:
        self._data.clear()

    # Additional helpers used by tests
    def load_dataframe(self, filename: str) -> pd.DataFrame:
        return self._data[filename].copy()

    def wait_for_pending_saves(self) -> None:  # pragma: no cover - no async work
        return None


@pytest.fixture
def fake_upload_storage(monkeypatch: pytest.MonkeyPatch) -> Generator[_FakeUploadStorage, None, None]:
    """Provide an in-memory upload storage fake."""

    store = _FakeUploadStorage()
    import utils.upload_store as upload_store_module

    monkeypatch.setattr(upload_store_module, "UploadedDataStore", lambda *a, **k: store)
    monkeypatch.setattr(upload_store_module, "uploaded_data_store", store)

    yield store

    store.clear_all()


class _FakeConfig(ConfigurationProtocol):
    """Simple fake implementing :class:`ConfigurationProtocol`."""

    def __init__(self) -> None:
        self.database: dict[str, Any] = {}
        self.app: dict[str, Any] = {}
        self.security: dict[str, Any] = {}
        self.upload: dict[str, Any] = {}

    def get_database_config(self) -> dict[str, Any]:
        return self.database

    def get_app_config(self) -> dict[str, Any]:
        return self.app

    def get_security_config(self) -> dict[str, Any]:
        return self.security

    def get_upload_config(self) -> dict[str, Any]:
        return self.upload

    def reload_config(self) -> None:
        return None

    def validate_config(self) -> dict[str, Any]:
        return {}


@pytest.fixture
def fake_config_provider() -> Generator[_FakeConfig, None, None]:
    """Yield a fresh fake configuration provider for each test."""

    cfg = _FakeConfig()
    yield cfg
    cfg.database.clear()
    cfg.app.clear()
    cfg.security.clear()
    cfg.upload.clear()


class _FakeLearningService:
    """Lightweight fake for device learning service."""

    def __init__(self) -> None:
        self.mappings: dict[str, dict[str, Any]] = {}

    def save_device_mappings(self, df: pd.DataFrame, filename: str, device_mappings: dict[str, Any]) -> str:
        self.mappings[filename] = device_mappings
        return "test_fp"

    def get_learned_mappings(self, df: pd.DataFrame, filename: str) -> dict[str, Any]:
        return self.mappings.get(filename, {})

    def apply_learned_mappings_to_global_store(self, df: pd.DataFrame, filename: str) -> bool:
        return bool(self.mappings.get(filename))

    def save_user_device_mappings(self, df: pd.DataFrame, filename: str, mappings: dict[str, Any]) -> bool:
        self.mappings[filename] = mappings
        return True

    def get_user_device_mappings(self, filename: str) -> dict[str, Any]:
        return self.mappings.get(filename, {})


@pytest.fixture
def fake_device_learning_service(monkeypatch: pytest.MonkeyPatch) -> Generator[_FakeLearningService, None, None]:
    """Provide a fake device learning service accessible via the usual import path."""

    service = _FakeLearningService()
    import types, sys

    module = types.ModuleType("services.device_learning_service")
    module.get_device_learning_service = lambda: service
    monkeypatch.setitem(sys.modules, "services.device_learning_service", module)

    yield service

    service.mappings.clear()
