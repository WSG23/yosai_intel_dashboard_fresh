# core/interfaces.py
"""Protocol definitions for configuration and analytics providers."""

from abc import abstractmethod
from typing import Any, Dict, Protocol

from yosai_intel_dashboard.src.core.protocols import ConfigurationServiceProtocol


class ConfigurationProviderProtocol(Protocol):
    """Provide configuration sections for various subsystems."""

    @abstractmethod
    def get_analytics_config(self) -> Dict[str, Any]:
        """Return analytics configuration section."""
        ...

    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """Return database configuration section."""
        ...

    @abstractmethod
    def get_security_config(self) -> Dict[str, Any]:
        """Return security configuration section."""
        ...


class AnalyticsProviderProtocol(Protocol):
    """Perform analytics operations and retrieve metrics."""

    @abstractmethod
    def process_dataframe(self, data: Any) -> Any:
        """Process raw analytics data and return a result."""
        ...

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Return computed analytics metrics."""
        ...


class ConfigProviderProtocol(Protocol):
    """Provide direct access to configuration objects."""

    @property
    @abstractmethod
    def analytics(self) -> Any:
        """Return analytics configuration object."""

    @property
    @abstractmethod
    def database(self) -> Any:
        """Return database configuration object."""

    @property
    @abstractmethod
    def security(self) -> Any:
        """Return security configuration object."""


__all__ = [
    "ConfigurationProviderProtocol",
    "AnalyticsProviderProtocol",
    "ConfigProviderProtocol",
    "ConfigurationServiceProtocol",
]
