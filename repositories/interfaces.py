"""Repository interfaces for data access layer.

See ADR-0004 for repository pattern rationale.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from yosai_intel_dashboard.src.core.domain.entities import AccessEvent, Door, Person


class IPersonRepository(ABC):
    """Person repository interface"""

    @abstractmethod
    async def get_by_id(self, person_id: str) -> Optional[Person]:
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Person]:
        pass

    @abstractmethod
    async def create(self, person: Person) -> Person:
        pass

    @abstractmethod
    async def update(self, person: Person) -> Person:
        pass

    @abstractmethod
    async def delete(self, person_id: str) -> bool:
        pass


class IAccessEventRepository(ABC):
    """Access event repository interface"""

    @abstractmethod
    async def get_events_by_person(
        self,
        person_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AccessEvent]:
        pass

    @abstractmethod
    async def get_events_by_door(
        self,
        door_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AccessEvent]:
        pass

    @abstractmethod
    async def create_event(self, event: AccessEvent) -> AccessEvent:
        pass

    @abstractmethod
    async def get_recent_events(self, limit: int = 100) -> List[AccessEvent]:
        pass


class IDoorRepository(ABC):
    """Door repository interface"""

    @abstractmethod
    async def get_by_id(self, door_id: str) -> Optional[Door]:
        pass

    @abstractmethod
    async def get_by_facility(self, facility_id: str) -> List[Door]:
        pass

    @abstractmethod
    async def get_critical_doors(self) -> List[Door]:
        pass
