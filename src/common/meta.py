"""Metaclasses and decorators for common patterns."""

from __future__ import annotations

from abc import ABCMeta
from typing import Any, Dict

from pydantic import BaseModel, ValidationError, validator


class _RegistryEntry(BaseModel):
    """Pydantic model to validate registry entries."""

    name: str

    @validator("name")
    def _non_empty(cls, value: str) -> str:  # pragma: no cover - trivial
        if not value:
            raise ValueError("registry name must be a non-empty string")
        return value


class AutoRegister(ABCMeta):
    """Metaclass that auto-registers subclasses in a registry.

    Subclasses can define a ``registry_name`` attribute to be registered in the
    mapping specified by ``REGISTRY`` on any base class. ``REGISTRY`` is expected
    to be a ``dict[str, type]``.
    """

    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ) -> None:  # type: ignore[override]
        super().__init__(name, bases, namespace)  # type: ignore[misc]
        registry = getattr(cls, "REGISTRY", None)
        reg_name = getattr(cls, "registry_name", None)
        if registry is not None and reg_name is not None:
            try:
                entry = _RegistryEntry(name=str(reg_name))
            except ValidationError as exc:
                # Re-raise with clearer context
                raise exc
            registry[entry.name] = cls


__all__ = ["AutoRegister"]
