"""Test configuration and fixtures"""

import sys
from pathlib import Path
import types
import importlib


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

@pytest.fixture
def async_runner() -> Generator[callable, None, None]:
    """Run async coroutines in a dedicated event loop."""

    loop = asyncio.new_event_loop()
    yield lambda coro: loop.run_until_complete(coro)
    loop.close()


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
    dash_stub.no_update = None

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

    yield dash_stub


@pytest.fixture
def fake_dbc(monkeypatch: pytest.MonkeyPatch, request):
    """Provide a minimal dash_bootstrap_components substitute."""

    dbc_stub = types.ModuleType("dash_bootstrap_components")

    class _Comp:
        def __init__(self, *args, **kwargs):
            self.args = args
            for k, v in kwargs.items():
                setattr(self, k, v)

    for name in [
        "Navbar",
        "Container",
        "Row",
        "Col",
        "NavbarToggler",
        "Collapse",
        "DropdownMenu",
        "DropdownMenuItem",
        "Card",
        "Alert",
        "Modal",
        "Toast",
    ]:
        setattr(dbc_stub, name, _Comp)

    dbc_stub.themes = types.SimpleNamespace(BOOTSTRAP="bootstrap")

    monkeypatch.setitem(sys.modules, "dash_bootstrap_components", dbc_stub)
    if hasattr(request.module, "dbc"):
        monkeypatch.setattr(request.module, "dbc", dbc_stub, raising=False)

    yield dbc_stub
