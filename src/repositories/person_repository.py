from __future__ import annotations

"""Repository pattern for Person data access"""

from dataclasses import dataclass
from typing import Generic, List, Optional, Protocol, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Success(Generic[T]):
    value: T

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False


@dataclass(frozen=True)
class Failure(Generic[E]):
    error: E

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True


Result = Union[Success[T], Failure[E]]


def success(value: T) -> Success[T]:
    return Success(value)


def failure(error: E) -> Failure[E]:
    return Failure(error)


@dataclass(frozen=True)
class Person:
    """Minimal person model for repository testing"""

    person_id: str
    name: str | None = None
    department: str | None = None

    def validate(self) -> Result[bool, str]:
        if not self.person_id:
            return failure("person_id cannot be empty")
        return success(True)


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
