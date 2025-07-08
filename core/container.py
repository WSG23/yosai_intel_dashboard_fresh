from __future__ import annotations

from typing import Any

from .service_container import ServiceContainer
from .protocols import (
    AnalyticsServiceProtocol,
    ConfigurationProtocol,
    UnicodeProcessorProtocol,
)

# Global container instance used across the application
container = ServiceContainer()


def get_config_provider() -> ConfigurationProtocol:
    """Return the registered :class:`ConfigurationProtocol` provider."""
    provider = container.get("config_manager", ConfigurationProtocol)
    if provider is None:
        raise RuntimeError("Configuration provider not registered")
    return provider


def get_analytics_provider() -> AnalyticsServiceProtocol:
    """Return the registered :class:`AnalyticsServiceProtocol` provider."""
    provider = container.get("analytics_service", AnalyticsServiceProtocol)
    if provider is None:
        raise RuntimeError("Analytics provider not registered")
    return provider


def get_unicode_processor() -> UnicodeProcessorProtocol:
    """Return the registered :class:`UnicodeProcessorProtocol` provider."""
    if container.has("unicode_processor"):
        return container.get("unicode_processor", UnicodeProcessorProtocol)

    from .unicode import UnicodeProcessor

    provider = UnicodeProcessor()
    container.register_singleton(
        "unicode_processor",
        provider,
        protocol=UnicodeProcessorProtocol,
    )
    return provider


# Backwards compatibility -------------------------------------------------
Container = ServiceContainer
