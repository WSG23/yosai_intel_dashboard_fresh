"""Placeholder repository implementations"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional

from yosai_intel_dashboard.src.utils.unicode_handler import UnicodeHandler
from yosai_intel_dashboard.src.core.domain.entities import AccessEvent, Door, Person
from yosai_intel_dashboard.src.core.domain.value_objects import AccessResult, BadgeStatus, DoorType

logger = logging.getLogger(__name__)
from database.types import DatabaseConnection

from .interfaces import IAccessEventRepository, IDoorRepository, IPersonRepository


def _sanitize(value: Optional[str]) -> Optional[str]:
    return UnicodeHandler.sanitize(value) if value is not None else None


def _row_to_person(row: dict) -> Person:
    row = {k: UnicodeHandler.sanitize(v) for k, v in row.items()}
    return Person(
        person_id=row["person_id"],
        name=row.get("name"),
        employee_id=row.get("employee_id"),
        department=row.get("department"),
        clearance_level=int(row.get("clearance_level", 1)),
        access_groups=(
            tuple(row.get("access_groups", "").split(","))
            if row.get("access_groups")
            else tuple()
        ),
        is_visitor=bool(row.get("is_visitor")),
        host_person_id=row.get("host_person_id"),
        created_at=(
            datetime.fromisoformat(row["created_at"])
            if row.get("created_at")
            else datetime.now()
        ),
        last_active=(
            datetime.fromisoformat(row["last_active"])
            if row.get("last_active")
            else None
        ),
        risk_score=float(row.get("risk_score", 0.0)),
    )


def _row_to_event(row: dict) -> AccessEvent:
    row = {k: UnicodeHandler.sanitize(v) for k, v in row.items()}
    return AccessEvent(
        event_id=row["event_id"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        person_id=row.get("person_id"),
        door_id=row.get("door_id"),
        badge_id=row.get("badge_id"),
        access_result=AccessResult(row["access_result"]),
        badge_status=BadgeStatus(row.get("badge_status", BadgeStatus.VALID.value)),
        door_held_open_time=float(row.get("door_held_open_time", 0.0)),
        entry_without_badge=bool(row.get("entry_without_badge")),
        device_status=row.get("device_status", ""),
        raw_data=json.loads(row.get("raw_data")) if row.get("raw_data") else {},
    )


def _row_to_door(row: dict) -> Door:
    row = {k: UnicodeHandler.sanitize(v) for k, v in row.items()}
    return Door(
        door_id=row["door_id"],
        door_name=row.get("door_name"),
        facility_id=row.get("facility_id"),
        area_id=row.get("area_id"),
        floor=row.get("floor"),
        door_type=DoorType(row.get("door_type", DoorType.STANDARD.value)),
        required_clearance=int(row.get("required_clearance", 1)),
        is_critical=bool(row.get("is_critical")),
        location_coordinates=None,
        device_id=row.get("device_id"),
        is_active=bool(row.get("is_active", True)),
        created_at=(
            datetime.fromisoformat(row["created_at"])
            if row.get("created_at")
            else datetime.now()
        ),
    )


class PersonRepository(IPersonRepository):
    """Database backed ``Person`` repository."""

    def __init__(self, connection: "DatabaseConnection") -> None:
        self.conn = connection

    # --------------------------------------------------------------
    async def get_by_id(self, person_id: str) -> Optional[Person]:
        query = "SELECT * FROM people WHERE person_id = %s"

        rows = await asyncio.to_thread(self.conn.execute_query, query, (person_id,))
        if rows:
            return _row_to_person(rows[0])
        return None

    # --------------------------------------------------------------
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Person]:
        query = "SELECT * FROM people ORDER BY person_id LIMIT %s OFFSET %s"
        rows = await asyncio.to_thread(self.conn.execute_query, query, (limit, offset))
        return [_row_to_person(r) for r in rows]

    # --------------------------------------------------------------
    async def create(self, person: Person) -> Person:
        query = (
            "INSERT INTO people (person_id, name, employee_id, department, "
            "clearance_level, access_groups, is_visitor, host_person_id, "
            "created_at, last_active, risk_score) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            _sanitize(person.person_id),
            _sanitize(person.name),
            _sanitize(person.employee_id),
            _sanitize(person.department),
            person.clearance_level,
            _sanitize(",".join(person.access_groups)),
            int(person.is_visitor),
            _sanitize(person.host_person_id),
            person.created_at.isoformat(),
            person.last_active.isoformat() if person.last_active else None,
            person.risk_score,
        )
        logger.info("Sanitized query: %s", query)
        await asyncio.to_thread(self.conn.execute_command, query, params)
        return person

    # --------------------------------------------------------------
    async def update(self, person: Person) -> Person:
        query = (
            "UPDATE people SET name=%s, employee_id=%s, department=%s, "
            "clearance_level=%s, access_groups=%s, is_visitor=%s, host_person_id=%s, "
            "last_active=%s, risk_score=%s WHERE person_id=%s"
        )
        params = (
            _sanitize(person.name),
            _sanitize(person.employee_id),
            _sanitize(person.department),
            person.clearance_level,
            _sanitize(",".join(person.access_groups)),
            int(person.is_visitor),
            _sanitize(person.host_person_id),
            person.last_active.isoformat() if person.last_active else None,
            person.risk_score,
            _sanitize(person.person_id),
        )
        logger.info("Sanitized query: %s", query)
        await asyncio.to_thread(self.conn.execute_command, query, params)
        return person

    # --------------------------------------------------------------
    async def delete(self, person_id: str) -> bool:
        query = "DELETE FROM people WHERE person_id=%s"
        person_id = _sanitize(person_id)
        logger.info("Sanitized query: %s", query)
        await asyncio.to_thread(self.conn.execute_command, query, (person_id,))
        return True


class AccessEventRepository(IAccessEventRepository):
    """Repository for ``AccessEvent`` records."""

    def __init__(self, connection: "DatabaseConnection") -> None:
        self.conn = connection

    # --------------------------------------------------------------
    async def get_events_by_person(
        self,
        person_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AccessEvent]:
        query_parts = ["SELECT * FROM access_events WHERE person_id=%s"]
        params: list = [person_id]
        if start_date:
            query_parts.append("AND timestamp >= %s")
            params.append(start_date.isoformat())
        if end_date:
            query_parts.append("AND timestamp <= %s")
            params.append(end_date.isoformat())
        query_parts.append("ORDER BY timestamp DESC LIMIT %s OFFSET %s")
        query = " ".join(query_parts)
        params.extend([limit, offset])

        rows = await asyncio.to_thread(self.conn.execute_query, query, tuple(params))
        return [_row_to_event(r) for r in rows]

    # --------------------------------------------------------------
    async def get_events_by_door(
        self,
        door_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AccessEvent]:
        query_parts = ["SELECT * FROM access_events WHERE door_id=%s"]
        params: list = [door_id]
        if start_date:
            query_parts.append("AND timestamp >= %s")
            params.append(start_date.isoformat())
        if end_date:
            query_parts.append("AND timestamp <= %s")
            params.append(end_date.isoformat())
        query_parts.append("ORDER BY timestamp DESC LIMIT %s OFFSET %s")
        query = " ".join(query_parts)
        params.extend([limit, offset])
        rows = await asyncio.to_thread(self.conn.execute_query, query, tuple(params))
        return [_row_to_event(r) for r in rows]

    # --------------------------------------------------------------
    async def create_event(self, event: AccessEvent) -> AccessEvent:
        query = (
            "INSERT INTO access_events (event_id, timestamp, person_id, door_id, "
            "badge_id, access_result, badge_status, door_held_open_time, "
            "entry_without_badge, device_status, raw_data, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            _sanitize(event.event_id),
            event.timestamp.isoformat(),
            _sanitize(event.person_id),
            _sanitize(event.door_id),
            _sanitize(event.badge_id),
            event.access_result.value,
            event.badge_status.value,
            event.door_held_open_time,
            int(event.entry_without_badge),
            _sanitize(event.device_status),
            json.dumps(event.raw_data),
            datetime.now().isoformat(),
        )
        logger.info("Sanitized query: %s", query)
        await asyncio.to_thread(self.conn.execute_command, query, params)
        return event

    # --------------------------------------------------------------
    async def get_recent_events(self, limit: int = 100) -> List[AccessEvent]:
        query = "SELECT * FROM access_events ORDER BY timestamp DESC LIMIT %s"
        rows = await asyncio.to_thread(self.conn.execute_query, query, (limit,))
        return [_row_to_event(r) for r in rows]


class DoorRepository(IDoorRepository):
    """Repository for ``Door`` entities."""

    def __init__(self, connection: "DatabaseConnection") -> None:
        self.conn = connection

    # --------------------------------------------------------------
    async def get_by_id(self, door_id: str) -> Optional[Door]:
        query = "SELECT * FROM doors WHERE door_id=%s"
        rows = await asyncio.to_thread(self.conn.execute_query, query, (door_id,))
        if rows:
            return _row_to_door(rows[0])
        return None

    # --------------------------------------------------------------
    async def get_by_facility(
        self, facility_id: str, *, limit: int = 100, offset: int = 0
    ) -> List[Door]:
        query = "SELECT * FROM doors WHERE facility_id=%s ORDER BY door_id LIMIT %s OFFSET %s"
        rows = await asyncio.to_thread(
            self.conn.execute_query, query, (facility_id, limit, offset)
        )
        return [_row_to_door(r) for r in rows]

    # --------------------------------------------------------------
    async def get_critical_doors(self) -> List[Door]:
        query = "SELECT * FROM doors WHERE is_critical=1"
        rows = await asyncio.to_thread(self.conn.execute_query, query)
        return [_row_to_door(r) for r in rows]
