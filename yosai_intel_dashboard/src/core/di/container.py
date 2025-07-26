from __future__ import annotations

import uuid
from typing import Any, Optional, Type

from core.service_container import ServiceContainer, ServiceLifetime


class DIContainer:
    """Lightweight wrapper around :class:`ServiceContainer`."""

    def __init__(self, container: Optional[ServiceContainer] = None) -> None:
        self._container = container or ServiceContainer()

    # ------------------------------------------------------------------
    def bind(
        self,
        key: str,
        implementation: Any,
        *,
        protocol: Optional[type] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        factory: Optional[Any] = None,
    ) -> "DIContainer":
        if lifetime is ServiceLifetime.SINGLETON:
            self._container.register_singleton(
                key, implementation, protocol=protocol, factory=factory
            )
        elif lifetime is ServiceLifetime.TRANSIENT:
            self._container.register_transient(
                key, implementation, protocol=protocol, factory=factory
            )
        elif lifetime is ServiceLifetime.SCOPED:
            self._container.register_scoped(
                key, implementation, protocol=protocol, factory=factory
            )
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unsupported lifetime: {lifetime}")
        return self

    # ------------------------------------------------------------------
    def resolve(self, key: str, protocol_type: Optional[Type[Any]] = None) -> Any:
        return self._container.get(key, protocol_type)

    # ------------------------------------------------------------------
    def create_scope(self, name: Optional[str] = None) -> "DIScope":
        return DIScope(self._container, name or str(uuid.uuid4()))


class DIScope:
    """Context manager for dependency injection scopes."""

    def __init__(self, container: ServiceContainer, name: str) -> None:
        self._container = container
        self._name = name
        self._previous: Optional[str] = None

    def __enter__(self) -> "DIScope":
        self._previous = self._container._current_scope
        self._container._current_scope = self._name
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._container._scoped_instances.pop(self._name, None)
        if self._previous is not None:
            self._container._current_scope = self._previous


__all__ = ["DIContainer", "DIScope"]
