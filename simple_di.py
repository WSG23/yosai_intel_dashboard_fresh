"""Minimal dependency injection utilities used in tests."""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, Type


class ServiceContainer:
    """Very small service registry."""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}
        self._type_map: dict[Type, str] = {}

    def register(self, key: str, instance: Any) -> None:
        self._services[key] = instance
        self._type_map[type(instance)] = key

    def get(self, key: str, typ: Type | None = None) -> Any:
        return self._services[key]

    def _find_service_for_type(self, typ: Type) -> str | None:
        return self._type_map.get(typ)


def inject(
    container: ServiceContainer,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator injecting arguments resolved from *container* by type."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(func)
        params = sig.parameters

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = sig.bind_partial(*args, **kwargs)
            for name, param in params.items():
                if name in bound.arguments:
                    continue
                if param.annotation is inspect.Parameter.empty:
                    continue
                service_key = container._find_service_for_type(param.annotation)
                if service_key and service_key not in bound.arguments:
                    kwargs[name] = container.get(service_key)
            return func(*args, **kwargs)

        return wrapper

    return decorator
