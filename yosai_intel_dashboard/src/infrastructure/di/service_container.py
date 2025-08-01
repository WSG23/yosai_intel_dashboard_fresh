"""Advanced dependency injection container with protocol support."""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    get_type_hints,
)

# Use the common BaseModel shared across the core package
from ...core.base_model import BaseModel

T = TypeVar("T")


class ServiceLifetime(Enum):
    """Service lifetime options."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceRegistration:
    service_type: Type
    implementation: Union[Type, Callable]
    protocol: Optional[type]
    lifetime: ServiceLifetime
    factory: Optional[Callable]
    dependencies: List[tuple[str, Type]]


class DependencyInjectionError(Exception):
    """Generic dependency injection error."""


class CircularDependencyError(DependencyInjectionError):
    """Raised when circular dependencies are detected."""


class ServiceContainer(BaseModel):
    """Protocol based dependency injection container."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self._services: Dict[str, ServiceRegistration] = {}
        self._instances: Dict[str, Any] = {}
        self._scoped_instances: Dict[str, Dict[str, Any]] = {}
        self._type_map: Dict[Type, str] = {}
        self._resolution_stack: List[str] = []
        self._health_checks: Dict[str, Callable[[Any], bool]] = {}
        self._current_scope: str = "default"

    # ------------------------------------------------------------------
    def register(
        self,
        service_key: str,
        instance: Any,
        *,
        protocol: Optional[type] = None,
    ) -> "ServiceContainer":
        """Compatibility helper mirroring :class:`DIContainer.register`."""
        self._services[service_key] = ServiceRegistration(
            service_type=type(instance),
            implementation=instance,
            protocol=protocol,
            lifetime=ServiceLifetime.SINGLETON,
            factory=None,
            dependencies=[],
        )
        self._instances[service_key] = instance
        self._type_map[type(instance)] = service_key
        if protocol:
            self._type_map[protocol] = service_key
        return self

    # ------------------------------------------------------------------
    def has(self, service_key: str) -> bool:
        """Return ``True`` if *service_key* is registered."""
        return service_key in self._services

    # ------------------------------------------------------------------
    def register_singleton(
        self,
        service_key: str,
        implementation: Any,
        protocol: Optional[type] = None,
        factory: Optional[Callable] = None,
    ) -> "ServiceContainer":
        """Register a singleton implementation or instance."""
        return self._register_service(
            service_key, implementation, protocol, ServiceLifetime.SINGLETON, factory
        )

    def register_transient(
        self,
        service_key: str,
        implementation: Any,
        protocol: Optional[type] = None,
        factory: Optional[Callable] = None,
    ) -> "ServiceContainer":
        return self._register_service(
            service_key, implementation, protocol, ServiceLifetime.TRANSIENT, factory
        )

    def register_scoped(
        self,
        service_key: str,
        implementation: Any,
        protocol: Optional[type] = None,
        factory: Optional[Callable] = None,
    ) -> "ServiceContainer":
        return self._register_service(
            service_key, implementation, protocol, ServiceLifetime.SCOPED, factory
        )

    # ------------------------------------------------------------------
    def _register_service(
        self,
        service_key: str,
        implementation: Any,
        protocol: Optional[type],
        lifetime: ServiceLifetime,
        factory: Optional[Callable],
    ) -> "ServiceContainer":
        deps = self._analyze_dependencies(implementation)
        reg = ServiceRegistration(
            service_type=(
                implementation
                if inspect.isclass(implementation)
                else type(implementation)
            ),
            implementation=implementation,
            protocol=protocol,
            lifetime=lifetime,
            factory=factory,
            dependencies=deps,
        )
        self._services[service_key] = reg
        self._type_map[reg.service_type] = service_key
        if protocol:
            self._type_map[protocol] = service_key
        return self

    # ------------------------------------------------------------------
    def _analyze_dependencies(self, implementation: Any) -> List[tuple[str, Type]]:
        if not inspect.isclass(implementation):
            return []

        init = implementation.__init__
        sig = inspect.signature(init)

        try:
            mod = inspect.getmodule(implementation)
            hints = get_type_hints(init, globalns=vars(mod) if mod else None)
        except Exception:
            hints = {}

        deps: List[tuple[str, Type]] = []
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            anno = hints.get(name, param.annotation)
            if anno != inspect.Parameter.empty:
                deps.append((name, anno))
        return deps

    # ------------------------------------------------------------------
    def get(self, service_key: str, protocol_type: Optional[Type[T]] = None) -> T:
        if service_key not in self._services:
            raise DependencyInjectionError(f"Service '{service_key}' not registered")
        if service_key in self._resolution_stack:
            cycle = " -> ".join(self._resolution_stack + [service_key])
            raise CircularDependencyError(f"Circular dependency detected: {cycle}")
        reg = self._services[service_key]
        if reg.lifetime == ServiceLifetime.SINGLETON:
            return self._get_singleton(service_key, reg, protocol_type)
        elif reg.lifetime == ServiceLifetime.TRANSIENT:
            return self._create_instance(service_key, reg, protocol_type)
        elif reg.lifetime == ServiceLifetime.SCOPED:
            return self._get_scoped(service_key, reg, protocol_type)
        else:  # pragma: no cover - defensive
            raise DependencyInjectionError("Unknown service lifetime")

    def _get_singleton(
        self, key: str, reg: ServiceRegistration, proto: Optional[type]
    ) -> Any:
        if key not in self._instances:
            self._instances[key] = self._create_instance(key, reg, proto)
        return self._instances[key]

    def _get_scoped(
        self, key: str, reg: ServiceRegistration, proto: Optional[type]
    ) -> Any:
        scope = self._scoped_instances.setdefault(self._current_scope, {})
        if key not in scope:
            scope[key] = self._create_instance(key, reg, proto)
        return scope[key]

    def _create_instance(
        self, key: str, reg: ServiceRegistration, proto: Optional[type]
    ) -> Any:
        self._resolution_stack.append(key)
        try:
            if reg.factory:
                instance = reg.factory(self)
            else:
                kwargs = self._resolve_dependencies(reg.dependencies)
                if inspect.isclass(reg.implementation):
                    instance = reg.implementation(**kwargs)
                else:
                    instance = reg.implementation
            if proto and not isinstance(instance, proto):
                raise DependencyInjectionError(
                    f"Service '{key}' does not implement protocol '{proto.__name__}'"
                )
            return instance
        finally:
            self._resolution_stack.pop()

    # ------------------------------------------------------------------
    def _resolve_dependencies(self, deps: List[tuple[str, Type]]) -> Dict[str, Any]:
        resolved: Dict[str, Any] = {}
        for name, dep_type in deps:
            svc_key = self._find_service_for_type(dep_type)
            if svc_key:
                resolved[name] = self.get(svc_key, dep_type)
        return resolved

    def _find_service_for_type(self, dep_type: Type) -> Optional[str]:
        if dep_type in self._type_map:
            return self._type_map[dep_type]
        for typ, key in self._type_map.items():
            try:
                if issubclass(typ, dep_type):
                    return key
            except Exception:
                continue
        return None

    # ------------------------------------------------------------------
    def register_health_check(
        self, service_key: str, check: Callable[[Any], bool]
    ) -> None:
        self._health_checks[service_key] = check

    def check_health(self) -> Dict[str, bool]:
        status: Dict[str, bool] = {}
        for key, func in self._health_checks.items():
            try:
                svc = self.get(key)
                status[key] = bool(func(svc))
            except Exception:
                status[key] = False
        return status

    # ------------------------------------------------------------------
    def warm_caches(self) -> None:
        """Trigger cache warming if a cache warmer service is registered."""
        if not self.has("cache_warmer"):
            return

        warmer = self.get("cache_warmer")
        if not hasattr(warmer, "warm"):
            return

        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(warmer.warm())
        else:
            asyncio.run_coroutine_threadsafe(warmer.warm(), loop).result()

    # ------------------------------------------------------------------
    def validate_registrations(self) -> Dict[str, List[str]]:
        results = {
            "valid": [],
            "missing_dependencies": [],
            "circular_dependencies": [],
            "protocol_violations": [],
        }
        for key, reg in self._services.items():
            try:
                self._create_instance(key, reg, reg.protocol)
                results["valid"].append(key)
            except CircularDependencyError:
                results["circular_dependencies"].append(key)
            except DependencyInjectionError as exc:
                msg = str(exc)
                if "not registered" in msg:
                    results["missing_dependencies"].append(key)
                elif "does not implement" in msg:
                    results["protocol_violations"].append(key)
        return results


__all__ = [
    "ServiceContainer",
    "ServiceLifetime",
    "DependencyInjectionError",
    "CircularDependencyError",
]
