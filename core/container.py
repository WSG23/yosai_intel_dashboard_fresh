"""Minimal dependency injection container."""

from __future__ import annotations

from typing import Any, Dict, Optional, Type

from .protocols import (
    AnalyticsServiceProtocol,
    ConfigurationProtocol,
    UnicodeProcessorProtocol,
)


class DIContainer:
    """Simple DI container supporting protocol-based registration."""

    def __init__(self) -> None:
        # Mapping of service name -> instance
        self._services: Dict[str, Any] = {}
        # Mapping of protocol -> name
        self._protocol_map: Dict[Type[Any], str] = {}

    # ------------------------------------------------------------------
    def initialize(self, services: Dict[Type[Any], Any]) -> None:
        """Register *services* validated against their protocol keys."""
        for protocol, instance in services.items():
            try:
                self.register(protocol.__name__, instance, protocol=protocol)
            except Exception as exc:  # pragma: no cover - defensive
                raise RuntimeError(
                    f"Failed to initialize service for {protocol}: {exc}"
                ) from exc

    # ------------------------------------------------------------------
    def register(
        self, name: str, service: Any, *, protocol: Optional[Type[Any]] = None
    ) -> None:
        """Register ``service`` under ``name`` with optional ``protocol``."""

        if protocol is not None:
            self._validate(service, protocol)
            self._protocol_map[protocol] = name
        self._services[name] = service

    # ------------------------------------------------------------------
    def get(self, key: str | Type[Any]) -> Any:
        """Retrieve a registered service by name or protocol."""

        if isinstance(key, str):
            return self._services.get(key)

        name = self._protocol_map.get(key)
        if name is None:
            return None
        return self._services.get(name)

    # ------------------------------------------------------------------
    def has(self, key: str | Type[Any]) -> bool:
        """Check if a service is registered under *key*."""

        if isinstance(key, str):
            return key in self._services
        return key in self._protocol_map

    # ------------------------------------------------------------------
    @staticmethod
    def _validate(service: Any, protocol: Type[Any]) -> None:
        """Validate ``service`` implements ``protocol`` when possible."""

        try:
            if not isinstance(service, protocol):  # type: ignore[arg-type]
                raise TypeError(f"Service {service!r} does not implement {protocol!r}")
        except TypeError:
            # ``protocol`` may not be runtime checkable; skip validation
            pass


# Global container instance used across the application
container = DIContainer()


def get_config_provider() -> ConfigurationProtocol:
    """Return the registered :class:`ConfigurationProtocol` provider."""

    provider = container.get(ConfigurationProtocol)
    if provider is None:
        raise RuntimeError("Configuration provider not registered")
    return provider


def get_analytics_provider() -> AnalyticsServiceProtocol:
    """Return the registered :class:`AnalyticsServiceProtocol` provider."""

    provider = container.get(AnalyticsServiceProtocol)
    if provider is None:
        raise RuntimeError("Analytics provider not registered")
    return provider


def get_unicode_processor() -> UnicodeProcessorProtocol:
    """Return the registered :class:`UnicodeProcessorProtocol` provider."""

    provider = container.get(UnicodeProcessorProtocol)
    if provider is None:
        from .unicode import UnicodeProcessor

        provider = UnicodeProcessor()
        container.register(
            "unicode_processor",
            provider,
            protocol=UnicodeProcessorProtocol,
        )
    return provider


# Backwards compatibility -------------------------------------------------
Container = DIContainer
