"""Unified protocol definitions for Yōsai Intel Dashboard."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    runtime_checkable,
)

import pandas as pd


@runtime_checkable
class DatabaseProtocol(Protocol):
    """Protocol defining database operations contract"""

    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        ...

    @abstractmethod
    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        """Execute a command (INSERT, UPDATE, DELETE)"""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Verify database connectivity"""
        ...


@runtime_checkable
class AnalyticsServiceProtocol(Protocol):
    """Protocol for analytics service operations"""

    @abstractmethod
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get main dashboard summary statistics"""
        ...

    @abstractmethod
    def analyze_access_patterns(self, days: int) -> Dict[str, Any]:
        """Analyze access patterns over specified days"""
        ...

    @abstractmethod
    def detect_anomalies(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in access data"""
        ...


@runtime_checkable
class ConfigurationProtocol(Protocol):
    """Protocol for configuration management"""

    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        ...

    @abstractmethod
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration"""
        ...

    @abstractmethod
    def reload_configuration(self) -> None:
        """Reload configuration from source"""
        ...


@runtime_checkable
class SerializationProtocol(Protocol):
    """Protocol for JSON serialization services"""

    @abstractmethod
    def serialize(self, data: Any) -> str:
        """Serialize data to a JSON string"""
        ...

    @abstractmethod
    def sanitize_for_transport(self, data: Any) -> Any:
        """Prepare data for network transport"""
        ...

    @abstractmethod
    def is_serializable(self, data: Any) -> bool:
        """Check if the given data can be serialized"""
        ...


@runtime_checkable
class CallbackProtocol(Protocol):
    """Protocol for services that wrap and validate callbacks"""

    @abstractmethod
    def handle_wrap(self, callback_func: Callable) -> Callable:
        """Return a wrapped, safe callback function"""
        ...

    @abstractmethod
    def validate_callback_output(self, output: Any) -> Any:
        """Validate and sanitize callback output"""
        ...


@runtime_checkable
class AnalyticsProtocol(Protocol):
    """Protocol for analytics services"""

    @abstractmethod
    def get_summary_stats(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics"""
        ...

    @abstractmethod
    def detect_anomalies(self, data: pd.DataFrame) -> pd.DataFrame:
        """Detect anomalies in data"""
        ...

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        ...


class PluginStatus(Enum):
    """Plugin lifecycle status"""

    DISCOVERED = "discovered"
    LOADED = "loaded"
    CONFIGURED = "configured"
    STARTED = "started"
    STOPPED = "stopped"
    FAILED = "failed"


class PluginPriority(Enum):
    """Plugin loading priority"""

    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 100


@dataclass
class PluginMetadata:
    """Plugin metadata definition"""

    name: str
    version: str
    description: str
    author: str
    priority: PluginPriority = PluginPriority.NORMAL
    dependencies: Optional[List[str]] = None
    config_section: Optional[str] = None
    enabled_by_default: bool = True
    min_yosai_version: Optional[str] = None
    max_yosai_version: Optional[str] = None


@runtime_checkable
class PluginProtocol(Protocol):
    """Core plugin protocol that all plugins must implement"""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata"""
        ...

    @abstractmethod
    def load(self, container: Any, config: Dict[str, Any]) -> bool:
        """Load and register plugin services with the DI container"""
        ...

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the plugin with provided settings"""
        ...

    @abstractmethod
    def start(self) -> bool:
        """Start the plugin"""
        ...

    @abstractmethod
    def stop(self) -> bool:
        """Stop the plugin gracefully"""
        ...

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return plugin health status"""
        ...


@runtime_checkable
class CallbackPluginProtocol(PluginProtocol, Protocol):
    """Protocol for plugins that register Dash callbacks"""

    @abstractmethod
    def register_callbacks(self, manager: Any, container: Any) -> bool:
        """Register callbacks with the application"""
        ...


@runtime_checkable
class ServicePluginProtocol(PluginProtocol, Protocol):
    """Protocol for plugins that provide services"""

    @abstractmethod
    def get_service_definitions(self) -> Dict[str, Any]:
        """Return service definitions for DI container registration"""
        ...


@runtime_checkable
class PluginManagerProtocol(Protocol):
    """Protocol for plugin management"""

    @abstractmethod
    def discover_plugins(self) -> List[PluginProtocol]:
        """Discover available plugins"""
        ...

    @abstractmethod
    def load_plugin(self, plugin: PluginProtocol) -> bool:
        """Load a specific plugin"""
        ...

    @abstractmethod
    def get_plugin_status(self, plugin_name: str) -> PluginStatus:
        """Get current status of a plugin"""
        ...
