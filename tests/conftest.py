"""Test configuration and fixtures"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
# Ensure test stubs (e.g., a Dash stub) are available before real packages
stub_dir = Path(__file__).resolve().parent / "stubs"
sys.path.insert(0, str(stub_dir))

import types
if "core.unicode_processor" not in sys.modules:
    _m = types.ModuleType("core.unicode_processor")

    class Dummy:
        pass

    _m.DefaultUnicodeProcessor = Dummy
    _m.safe_decode_bytes = lambda *a, **k: ""
    _m.safe_encode_text = lambda *a, **k: ""
    _m.safe_decode = lambda *a, **k: ""
    _m.safe_encode = lambda *a, **k: ""
    _m.sanitize_dataframe = lambda df, **k: df
    _m.sanitize_data_frame = lambda df, **k: df
    _m.handle_surrogate_characters = lambda t: t
    _m.clean_unicode_surrogates = lambda t: t
    _m.sanitize_unicode_input = lambda t: t
    _m.contains_surrogates = lambda t: False
    _m.process_large_csv_content = lambda *a, **k: ""
    _m.safe_format_number = lambda v: str(v)
    _m.UnicodeProcessor = Dummy
    _m.ChunkedUnicodeProcessor = Dummy
    _m.safe_unicode_encode = lambda t: t
    _m.sanitize_unicode_input = lambda t: t
    sys.modules["core.unicode_processor"] = _m

if "core.unicode" not in sys.modules:
    u = types.ModuleType("core.unicode")
    u.UnicodeProcessor = Dummy
    u.ChunkedUnicodeProcessor = Dummy
    u.UnicodeTextProcessor = Dummy
    u.UnicodeSQLProcessor = Dummy
    u.UnicodeSecurityProcessor = Dummy
    u.clean_unicode_text = lambda t: t
    u.safe_decode_bytes = lambda *a, **k: ""
    u.safe_encode_text = lambda *a, **k: ""
    u.sanitize_dataframe = lambda df, **k: df
    u.contains_surrogates = lambda t: False
    u.process_large_csv_content = lambda *a, **k: ""
    u.safe_format_number = lambda v: str(v)
    u.object_count = lambda items: 0
    u.safe_unicode_encode = lambda t: t
    u.sanitize_unicode_input = lambda t: t
    sys.modules["core.unicode"] = u

if "dash_bootstrap_components" not in sys.modules:
    dbc_stub = types.ModuleType("dash_bootstrap_components")
    dbc_stub.Navbar = dbc_stub.Container = dbc_stub.Row = dbc_stub.Col = (
        lambda *a, **k: None
    )
    dbc_stub.NavbarToggler = dbc_stub.Collapse = dbc_stub.DropdownMenu = (
        lambda *a, **k: None
    )
    dbc_stub.DropdownMenuItem = lambda *a, **k: None
    sys.modules["dash_bootstrap_components"] = dbc_stub

if "plotly" not in sys.modules:
    plotly = types.ModuleType("plotly")
    plotly.express = types.ModuleType("plotly.express")
    plotly.graph_objects = types.ModuleType("plotly.graph_objects")
    sys.modules["plotly"] = plotly
    sys.modules["plotly.express"] = plotly.express
    sys.modules["plotly.graph_objects"] = plotly.graph_objects

import shutil
import tempfile
from typing import Any, Generator

import pandas as pd
import pytest
import asyncio

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
def upload_data_service(tmp_path: Path):
    """Provide a fresh ``UploadDataService`` backed by a temp store."""

    from utils.upload_store import UploadedDataStore
    from services.upload_data_service import UploadDataService

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

    loop = asyncio.new_event_loop()
    yield lambda coro: loop.run_until_complete(coro)
    loop.close()
