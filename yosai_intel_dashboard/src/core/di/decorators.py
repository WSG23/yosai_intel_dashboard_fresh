from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, Optional, Type

from yosai_intel_dashboard.src.core.container import container as _global_container
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer, ServiceLifetime

# ---------------------------------------------------------------------------


def injectable(
    cls: Optional[Type] = None,
    *,
    key: Optional[str] = None,
    protocol: Optional[type] = None,
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    container: Optional[ServiceContainer] = None,
) -> Callable[[Type], Type] | Type:
    """Register *cls* with the DI container using the given lifetime."""

    def decorator(target: Type) -> Type:
        cont = container or _global_container
        service_key = key or target.__name__.lower()
        if lifetime == ServiceLifetime.SINGLETON:
            cont.register_singleton(service_key, target, protocol=protocol)
        else:
            cont.register_transient(service_key, target, protocol=protocol)
        setattr(target, "_di_service_key", service_key)
        setattr(target, "_di_lifetime", lifetime)
        if protocol:
            setattr(target, "_di_protocol", protocol)
        return target

    if cls is None:
        return decorator
    return decorator(cls)


# ---------------------------------------------------------------------------


def singleton(
    cls: Optional[Type] = None,
    *,
    key: Optional[str] = None,
    protocol: Optional[type] = None,
    container: Optional[ServiceContainer] = None,
) -> Callable[[Type], Type] | Type:
    """Class decorator registering a singleton service."""

    return injectable(
        cls,
        key=key,
        protocol=protocol,
        lifetime=ServiceLifetime.SINGLETON,
        container=container,
    )


def transient(
    cls: Optional[Type] = None,
    *,
    key: Optional[str] = None,
    protocol: Optional[type] = None,
    container: Optional[ServiceContainer] = None,
) -> Callable[[Type], Type] | Type:
    """Class decorator registering a transient service."""

    return injectable(
        cls,
        key=key,
        protocol=protocol,
        lifetime=ServiceLifetime.TRANSIENT,
        container=container,
    )


# ---------------------------------------------------------------------------


def inject(
    func: Optional[Callable[..., Any]] = None,
    *,
    container: Optional[ServiceContainer] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]] | Callable[..., Any]:
    """Inject dependencies resolved from the DI container."""

    def decorator(target: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(target)
        params = sig.parameters

        @wraps(target)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = sig.bind_partial(*args, **kwargs)
            cont = container or _global_container
            for name, param in params.items():
                if name in bound.arguments:
                    continue
                if param.annotation is inspect.Parameter.empty:
                    continue
                if name in ("self", "cls"):
                    continue
                find = getattr(cont, "_find_service_for_type", None)
                service_key = find(param.annotation) if callable(find) else None
                if service_key:
                    kwargs[name] = cont.get(service_key, param.annotation)
            return target(*args, **kwargs)

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


__all__ = ["injectable", "inject", "singleton", "transient"]
