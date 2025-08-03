"""Cross-cutting mixins for logging and serialization concerns."""
from __future__ import annotations

import logging
from typing import Any, Dict, Protocol, Type, TypeVar, runtime_checkable


@runtime_checkable
class Loggable(Protocol):
    """Protocol for objects capable of logging messages."""

    def log(self, message: str) -> None:
        """Log ``message`` to the configured logger."""
        ...


T = TypeVar("T", bound="Serializable")


@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects supporting basic serialization."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object into a dictionary representation."""
        ...

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Recreate the object from a dictionary representation."""
        ...


class LoggingMixin:
    """Provide a convenience ``log`` method using ``logging``."""

    @property
    def logger(self) -> logging.Logger:
        """Return a module-level logger named for the concrete class."""
        return logging.getLogger(self.__class__.__name__)

    def log(self, message: str) -> None:
        """Log ``message`` with ``INFO`` severity."""
        self.logger.info(message)


class SerializationMixin:
    """Implement ``to_dict``/``from_dict`` helpers using ``__dict__``."""

    def to_dict(self) -> Dict[str, Any]:
        """Return a shallow copy of ``__dict__``."""
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Instantiate ``cls`` using ``data`` as keyword arguments."""
        return cls(**data)  # type: ignore[arg-type]


__all__ = [
    "Loggable",
    "Serializable",
    "LoggingMixin",
    "SerializationMixin",
]
