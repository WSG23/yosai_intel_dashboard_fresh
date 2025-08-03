import asyncio
import enum
import importlib
import sys
from datetime import datetime

import pytest
from tests.import_helpers import safe_import, import_optional

# Provide minimal Flask stub required by utility modules
if "flask" not in sys.modules:
    import types

    flask_stub = types.ModuleType("flask")
    flask_stub.request = None
    flask_stub.url_for = lambda *a, **k: ""
    safe_import('flask', flask_stub)

# Provide minimal ``utils.unicode_handler`` without importing heavy utils package
if "utils.unicode_handler" not in sys.modules:
    from importlib import machinery, util
    from pathlib import Path

    file_path = Path(__file__).resolve().parents[2] / "utils" / "unicode_handler.py"
    spec = util.spec_from_file_location("utils.unicode_handler", file_path)
    unicode_mod = util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(unicode_mod)
    utils_pkg = util.module_from_spec(machinery.ModuleSpec("utils", None))
    utils_pkg.unicode_handler = unicode_mod
    safe_import('utils', utils_pkg)
    safe_import('utils.unicode_handler', unicode_mod)

# Map project modules into the expected namespace if they aren't installed
if "yosai_intel_dashboard.src.core.domain.entities" not in sys.modules:
    sys.modules.setdefault(
        "yosai_intel_dashboard",
        importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec("yosai_intel_dashboard", None)
        ),
    )
    entities_stub = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("yosai_intel_dashboard.src.core.domain.entities", None)
    )
    enums_stub = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("yosai_intel_dashboard.src.core.domain.value_objects", None)
    )
    safe_import('yosai_intel_dashboard.models', importlib.util.module_from_spec()
        importlib.machinery.ModuleSpec("yosai_intel_dashboard.models", None)
    )
    safe_import('yosai_intel_dashboard.src.core.domain.entities', entities_stub)
    safe_import('yosai_intel_dashboard.src.core.domain.value_objects', enums_stub)

    class AccessResult(enum.Enum):
        GRANTED = "granted"

    class BadgeStatus(enum.Enum):
        VALID = "valid"

    class DoorType(enum.Enum):
        STANDARD = "standard"

    class Person:
        def __init__(self, person_id: str, name: str | None = None) -> None:
            self.person_id = person_id
            self.name = name

    class AccessEvent:
        def __init__(self, event_id: str, timestamp: datetime, **kwargs) -> None:
            self.event_id = event_id
            self.timestamp = timestamp
            self.person_id = kwargs.get("person_id")
            self.door_id = kwargs.get("door_id")
            self.badge_id = kwargs.get("badge_id")
            self.access_result = kwargs.get("access_result", AccessResult.GRANTED)
            self.badge_status = kwargs.get("badge_status", BadgeStatus.VALID)
            self.door_held_open_time = kwargs.get("door_held_open_time", 0.0)
            self.entry_without_badge = kwargs.get("entry_without_badge", False)
            self.device_status = kwargs.get("device_status", "")
            self.raw_data = kwargs.get("raw_data", {})

    class Door:
        def __init__(self, door_id: str, door_name: str | None = None) -> None:
            self.door_id = door_id
            self.door_name = door_name

    entities_stub.Person = Person
    entities_stub.AccessEvent = AccessEvent
    entities_stub.Door = Door
    enums_stub.AccessResult = AccessResult
    enums_stub.BadgeStatus = BadgeStatus
    enums_stub.DoorType = DoorType

from repositories.implementations import AccessEventRepository, PersonRepository
from yosai_intel_dashboard.src.core.domain.entities import AccessEvent, Person
from yosai_intel_dashboard.src.core.domain.value_objects import AccessResult, BadgeStatus


class RecordingConn:
    def __init__(self):
        self.last_query = None
        self.last_params = None

    def execute_query(self, query, params=None):
        self.last_query = query
        self.last_params = params
        return []

    def execute_command(self, command, params=None):
        self.last_query = command
        self.last_params = params
        return 0

    def execute_batch(self, command, params_seq):
        self.last_query = command
        self.last_params = params_seq
        return 0

    def health_check(self):
        return True


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.mark.asyncio
async def test_get_by_id_prevents_injection():
    conn = RecordingConn()
    repo = PersonRepository(conn)
    malicious = "P1'; DROP TABLE people;--"
    await repo.get_by_id(malicious)
    assert malicious in conn.last_params
    assert malicious not in conn.last_query


@pytest.mark.asyncio
async def test_create_event_prevents_injection():
    conn = RecordingConn()
    repo = AccessEventRepository(conn)
    event = AccessEvent(
        event_id="E1'; DROP TABLE x;--",
        timestamp=datetime.now(),
        person_id="P1",
        door_id="D1",
        badge_id=None,
        access_result=AccessResult.GRANTED,
        badge_status=BadgeStatus.VALID,
        door_held_open_time=0.0,
        entry_without_badge=False,
        device_status="normal",
        raw_data={},
    )
    await repo.create_event(event)
    assert event.event_id in conn.last_params
    assert "; DROP TABLE" not in conn.last_query
