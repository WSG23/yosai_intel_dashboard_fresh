"""Container bootstrap utilities."""
from __future__ import annotations

from core.service_container import ServiceContainer
from startup.service_registration import register_all_application_services
from startup.registry_startup import register_optional_services


def bootstrap_container() -> ServiceContainer:
    """Create and configure a :class:`ServiceContainer`."""
    container = ServiceContainer()
    register_all_application_services(container)
    register_optional_services()
    return container

__all__ = ["bootstrap_container"]
