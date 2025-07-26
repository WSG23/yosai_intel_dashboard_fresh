from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


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
    def metadata(self) -> PluginMetadata: ...

    def load(self, container: Any, config: Dict[str, Any]) -> bool: ...

    def configure(self, config: Dict[str, Any]) -> bool: ...

    def start(self) -> bool: ...

    def stop(self) -> bool: ...

    def health_check(self) -> Dict[str, Any]: ...


@runtime_checkable
class CallbackPluginProtocol(PluginProtocol, Protocol):
    """Protocol for plugins that register Dash callbacks"""

    def register_callbacks(self, manager: Any, container: Any) -> bool: ...


@runtime_checkable
class ServicePluginProtocol(PluginProtocol, Protocol):
    """Protocol for plugins that provide services"""

    def get_service_definitions(self) -> Dict[str, Any]: ...


@runtime_checkable
class PluginManagerProtocol(Protocol):
    """Protocol for plugin management"""

    def discover_plugins(self) -> List[PluginProtocol]: ...

    def load_plugin(self, plugin: PluginProtocol) -> bool: ...

    def get_plugin_status(self, plugin_name: str) -> PluginStatus: ...
