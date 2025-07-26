from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional


@dataclass
class ServiceInfo:
    """Basic service metadata for discovery."""

    name: str
    endpoint: str
    health_check: Callable[[], bool]


_registry: Dict[str, ServiceInfo] = {}


def register_service(name: str, endpoint: str, health_check: Callable[[], bool]) -> None:
    """Register a service with its endpoint and health check."""
    _registry[name] = ServiceInfo(name=name, endpoint=endpoint, health_check=health_check)


def discover_service(name: str) -> Optional[ServiceInfo]:
    """Return the :class:`ServiceInfo` for ``name`` if registered."""
    return _registry.get(name)


def health_check_all() -> Dict[str, bool]:
    """Run health checks for all registered services."""
    results: Dict[str, bool] = {}
    for name, info in _registry.items():
        try:
            results[name] = bool(info.health_check())
        except Exception:
            results[name] = False
    return results
