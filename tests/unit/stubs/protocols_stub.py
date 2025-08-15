from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


class PluginStatus(Enum):
    DISCOVERED = "discovered"
    LOADED = "loaded"
    CONFIGURED = "configured"
    STARTED = "started"
    STOPPED = "stopped"
    FAILED = "failed"


class PluginPriority(Enum):
    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 100


@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str
    author: str
    priority: PluginPriority = PluginPriority.NORMAL
    dependencies: Optional[List[str]] = None


@runtime_checkable
class PluginProtocol(Protocol):
    @property
    def metadata(self) -> PluginMetadata: ...
    def load(self, container: Any, config: Dict[str, Any]) -> bool: ...
    def configure(self, config: Dict[str, Any]) -> bool: ...
    def start(self) -> bool: ...
    def stop(self) -> bool: ...
    def health_check(self) -> Dict[str, Any]: ...


@runtime_checkable
class CallbackPluginProtocol(PluginProtocol, Protocol):
    def register_callbacks(self, manager: Any, container: Any) -> bool: ...
