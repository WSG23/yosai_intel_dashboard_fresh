"""Placeholder repository implementations"""

from datetime import datetime
from typing import List, Optional

from models.entities import AccessEvent, Door, Person

from .interfaces import IAccessEventRepository, IDoorRepository, IPersonRepository


class PersonRepository(IPersonRepository):
    async def get_by_id(self, person_id: str) -> Optional[Person]:  # pragma: no cover
        raise NotImplementedError

    async def get_all(
        self, limit: int = 100, offset: int = 0
    ) -> List[Person]:  # pragma: no cover
        raise NotImplementedError

    async def create(self, person: Person) -> Person:  # pragma: no cover
        raise NotImplementedError

    async def update(self, person: Person) -> Person:  # pragma: no cover
        raise NotImplementedError

    async def delete(self, person_id: str) -> bool:  # pragma: no cover
        raise NotImplementedError


class AccessEventRepository(IAccessEventRepository):
    async def get_events_by_person(
        self,
        person_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AccessEvent]:  # pragma: no cover
        raise NotImplementedError

    async def get_events_by_door(
        self,
        door_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AccessEvent]:  # pragma: no cover
        raise NotImplementedError

    async def create_event(self, event: AccessEvent) -> AccessEvent:  # pragma: no cover
        raise NotImplementedError

    async def get_recent_events(
        self, limit: int = 100
    ) -> List[AccessEvent]:  # pragma: no cover
        raise NotImplementedError


class DoorRepository(IDoorRepository):
    async def get_by_id(self, door_id: str) -> Optional[Door]:  # pragma: no cover
        raise NotImplementedError

    async def get_by_facility(self, facility_id: str) -> List[Door]:  # pragma: no cover
        raise NotImplementedError

    async def get_critical_doors(self) -> List[Door]:  # pragma: no cover
        raise NotImplementedError
