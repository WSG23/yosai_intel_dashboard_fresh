# core/interfaces.py
"""Protocol definitions for configuration and analytics providers."""

from abc import abstractmethod
from typing import Any, Dict, Protocol


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
    def process_data(self, data: Any) -> Any:
        """Process raw analytics data and return a result."""
        ...

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Return computed analytics metrics."""
        ...
