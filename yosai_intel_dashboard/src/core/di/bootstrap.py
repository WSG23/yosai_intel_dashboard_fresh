"""Application service container bootstrap."""

from __future__ import annotations

from core.service_container import ServiceContainer as DIContainer
from config.complete_service_registration import register_all_application_services


def bootstrap_container() -> DIContainer:
    """Create and configure the application-wide DI container."""
    container = DIContainer()
    register_all_application_services(container)
    return container


__all__ = ["bootstrap_container"]
