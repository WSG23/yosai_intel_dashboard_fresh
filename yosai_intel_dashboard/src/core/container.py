from __future__ import annotations

from typing import Any
import warnings

from .protocols import (
    AnalyticsServiceProtocol,
    ConfigurationProtocol,
    UnicodeProcessorProtocol,
)
from .service_container import ServiceContainer

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


class Container(ServiceContainer):
    """Deprecated alias for :class:`ServiceContainer`."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[override]
        warnings.warn(
            "Container is deprecated; use ServiceContainer",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
