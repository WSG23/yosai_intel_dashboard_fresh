# core/plugins/protocols.py
"""
Plugin system protocols for Yōsai Intel Dashboard
Follows the existing protocol-oriented architecture
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Type, runtime_checkable


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

    CRITICAL = 0  # Core functionality plugins
    HIGH = 10  # Important feature plugins
    NORMAL = 50  # Standard feature plugins
    LOW = 100  # Optional enhancement plugins


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
        """Start the plugin (if it has runtime components)"""
        ...

    @abstractmethod
    def stop(self) -> bool:
        """Stop the plugin gracefully"""
        ...

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return plugin health status used for monitoring"""
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
