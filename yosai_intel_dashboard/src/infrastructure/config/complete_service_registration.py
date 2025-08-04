"""Compatibility wrapper for application service registration."""

from __future__ import annotations

from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from startup import service_registration
import warnings


def register_all_application_services(container: ServiceContainer) -> None:
    """Register all application services with the container."""

    service_registration.register_all_application_services(container)


def register_all_services(container: ServiceContainer) -> None:
    """Backward compatible alias for register_all_application_services."""
    warnings.warn(
        "register_all_services is deprecated; use register_all_application_services",
        DeprecationWarning,
        stacklevel=2,
    )
    service_registration.register_all_application_services(container)


__all__ = [
    "register_all_application_services",
    "register_all_services",
]
