"""Repository pattern for Person data access"""

from dataclasses import dataclass
from typing import List, Optional, Protocol

from utils.result_types import Result, failure, success
from yosai_intel_dashboard.models.entities import Person


class PersonRepositoryProtocol(Protocol):
    def find_by_id(self, person_id: str) -> Result[Optional[Person], str]: ...

    def find_by_department(self, department: str) -> Result[List[Person], str]: ...

    def save(self, person: Person) -> Result[Person, str]: ...


class InMemoryPersonRepository(PersonRepositoryProtocol):
    def __init__(self) -> None:
        self._people: dict[str, Person] = {}

    def find_by_id(self, person_id: str) -> Result[Optional[Person], str]:
        try:
            return success(self._people.get(person_id))
        except Exception as e:
            return failure(f"Error finding person: {e}")

    def find_by_department(self, department: str) -> Result[List[Person], str]:
        try:
            people = [p for p in self._people.values() if p.department == department]
            return success(people)
        except Exception as e:
            return failure(f"Error finding people: {e}")

    def save(self, person: Person) -> Result[Person, str]:
        try:
            validation = person.validate()
            if validation.is_failure():
                return failure(f"Invalid person: {validation.error}")
            self._people[person.person_id] = person
            return success(person)
        except Exception as e:
            return failure(f"Error saving person: {e}")
