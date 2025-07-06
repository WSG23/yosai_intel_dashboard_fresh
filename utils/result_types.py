"""Result types for functional error handling"""

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True)
class Success(Generic[T]):
    value: T

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False

    def map(self, func: Callable[[T], U]) -> "Result[U, E]":
        try:
            return Success(func(self.value))
        except Exception as e:
            return Failure(e)


@dataclass(frozen=True)
class Failure(Generic[E]):
    error: E

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True

    def map(self, func: Callable) -> "Result[T, E]":
        return self


Result = Union[Success[T], Failure[E]]


def success(value: T) -> Success[T]:
    return Success(value)


def failure(error: E) -> Failure[E]:
    return Failure(error)
