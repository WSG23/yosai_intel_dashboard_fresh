"""Container bootstrap utilities."""
from __future__ import annotations

from core.service_container import ServiceContainer
from startup.service_registration import register_all_application_services


def bootstrap_container() -> ServiceContainer:
    """Create and configure a :class:`ServiceContainer`."""
    container = ServiceContainer()
    register_all_application_services(container)
    return container

__all__ = ["bootstrap_container"]
