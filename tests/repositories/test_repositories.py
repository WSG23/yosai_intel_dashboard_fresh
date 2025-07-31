import sqlite3
from datetime import datetime, timedelta

import pytest

from repositories.implementations import (
    AccessEventRepository,
    DoorRepository,
    PersonRepository,
)
from yosai_intel_dashboard.src.core.domain.entities import AccessEvent, Door, Person
from yosai_intel_dashboard.src.core.domain.value_objects import AccessResult, BadgeStatus, DoorType


class _SQLiteConn:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    @staticmethod
    def _adapt(sql: str) -> str:
        return sql.replace("%s", "?")

    def execute_query(self, query: str, params: tuple | None = None):
        cur = self.conn.cursor()
        cur.execute(self._adapt(query), params or ())
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def execute_command(self, command: str, params: tuple | None = None):
        cur = self.conn.cursor()
        cur.execute(self._adapt(command), params or ())
        self.conn.commit()
        return cur.rowcount

    def health_check(self) -> bool:
        try:
            self.conn.execute("SELECT 1")
            return True
        except Exception:
            return False


@pytest.fixture()
def db():
    c = _SQLiteConn()
    # create tables
    c.execute_command(
        """CREATE TABLE people (
               person_id TEXT PRIMARY KEY,
               name TEXT,
               employee_id TEXT,
               department TEXT,
               clearance_level INTEGER,
               access_groups TEXT,
               is_visitor INTEGER,
               host_person_id TEXT,
               created_at TEXT,
               last_active TEXT,
               risk_score REAL
           )"""
    )
    c.execute_command(
        """CREATE TABLE doors (
               door_id TEXT PRIMARY KEY,
               door_name TEXT,
               facility_id TEXT,
               area_id TEXT,
               floor TEXT,
               door_type TEXT,
               required_clearance INTEGER,
               is_critical INTEGER,
               location_coordinates TEXT,
               device_id TEXT,
               is_active INTEGER,
               created_at TEXT
           )"""
    )
    c.execute_command(
        """CREATE TABLE access_events (
               event_id TEXT PRIMARY KEY,
               timestamp TEXT,
               person_id TEXT,
               door_id TEXT,
               badge_id TEXT,
               access_result TEXT,
               badge_status TEXT,
               door_held_open_time REAL,
               entry_without_badge INTEGER,
               device_status TEXT,
               raw_data TEXT,
               created_at TEXT
           )"""
    )
    yield c
    c.conn.close()


def test_person_repository_crud(async_runner, db):
    repo = PersonRepository(db)
    p1 = Person(person_id="P1", name="Alpha")
    async_runner(repo.create(p1))
    fetched = async_runner(repo.get_by_id("P1"))
    assert fetched == p1

    p2 = Person(person_id="P2", name="Beta")
    async_runner(repo.create(p2))

    all_people = async_runner(repo.get_all(limit=1, offset=1))
    assert len(all_people) == 1
    assert all_people[0] == p2

    updated = Person(
        person_id="P1",
        name="Gamma",
        clearance_level=1,
        created_at=fetched.created_at,
    )
    async_runner(repo.update(updated))
    fetched2 = async_runner(repo.get_by_id("P1"))
    assert fetched2.name == "Gamma"

    async_runner(repo.delete("P1"))
    assert async_runner(repo.get_by_id("P1")) is None


def _insert_door(db, door: Door):
    db.execute_command(
        "INSERT INTO doors (door_id, door_name, facility_id, area_id, door_type, required_clearance, is_critical, is_active, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            door.door_id,
            door.door_name,
            door.facility_id,
            door.area_id,
            door.door_type.value,
            door.required_clearance,
            int(door.is_critical),
            int(door.is_active),
            door.created_at.isoformat(),
        ),
    )


def test_door_repository(async_runner, db):
    repo = DoorRepository(db)
    d1 = Door(door_id="D1", door_name="Front", facility_id="F1", area_id="A1")
    d2 = Door(
        door_id="D2", door_name="Side", facility_id="F1", area_id="A1", is_critical=True
    )
    _insert_door(db, d1)
    _insert_door(db, d2)

    door = async_runner(repo.get_by_id("D1"))
    assert door.door_name == "Front"

    doors = async_runner(repo.get_by_facility("F1"))
    assert len(doors) == 2

    critical = async_runner(repo.get_critical_doors())
    assert any(d.door_id == "D2" for d in critical)


def test_access_event_repository(async_runner, db):
    person_repo = PersonRepository(db)
    door_repo = DoorRepository(db)
    event_repo = AccessEventRepository(db)

    p = Person(person_id="P1", name="Tester")
    async_runner(person_repo.create(p))
    d = Door(door_id="D1", door_name="Main", facility_id="F1", area_id="A1")
    _insert_door(db, d)

    now = datetime.now()
    e1 = AccessEvent(
        event_id="E1",
        timestamp=now - timedelta(minutes=1),
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
    e2 = AccessEvent(
        event_id="E2",
        timestamp=now,
        person_id="P1",
        door_id="D1",
        badge_id=None,
        access_result=AccessResult.DENIED,
        badge_status=BadgeStatus.VALID,
        door_held_open_time=0.0,
        entry_without_badge=False,
        device_status="normal",
        raw_data={},
    )
    async_runner(event_repo.create_event(e1))
    async_runner(event_repo.create_event(e2))

    by_person = async_runner(event_repo.get_events_by_person("P1", limit=1))
    assert len(by_person) == 1

    by_door = async_runner(event_repo.get_events_by_door("D1"))
    assert len(by_door) == 2

    recent = async_runner(event_repo.get_recent_events(limit=1))
    assert recent[0].event_id == "E2"
