from __future__ import annotations

import atexit
import sys
import time
import types
from enum import Enum
from typing import Any, Dict, Protocol

import pytest

from yosai_intel_dashboard.src.core.imports.resolver import safe_import
from yosai_intel_dashboard.src.infrastructure.config import create_config_manager
from yosai_intel_dashboard.src.infrastructure.di.service_container import (
    ServiceContainer,
)


def _install_protocol_stubs(monkeypatch: "pytest.MonkeyPatch") -> None:
    """Install minimal protocol stubs under services.data_processing.core."""

    protocols = types.ModuleType("core.protocols.plugin")

    class PluginPriority(Enum):
        CRITICAL = 0
        HIGH = 10
        NORMAL = 50
        LOW = 100

    class PluginStatus(Enum):
        DISCOVERED = "discovered"
        LOADED = "loaded"
        CONFIGURED = "configured"
        STARTED = "started"
        STOPPED = "stopped"
        FAILED = "failed"

    class PluginProtocol(Protocol):
        metadata: Any

        def load(self, container: Any, config: Dict[str, Any]) -> bool: ...

        def configure(self, config: Dict[str, Any]) -> bool: ...

        def start(self) -> bool: ...

        def stop(self) -> bool: ...

        def health_check(self) -> Dict[str, Any]: ...

    class CallbackPluginProtocol(PluginProtocol, Protocol):
        def register_callbacks(self, manager: Any, container: Any) -> Any: ...

    protocols.PluginPriority = PluginPriority
    protocols.PluginStatus = PluginStatus
    protocols.PluginProtocol = PluginProtocol
    protocols.CallbackPluginProtocol = CallbackPluginProtocol

    services_pkg = types.ModuleType("services")
    services_pkg.__path__ = []
    data_processing_pkg = types.ModuleType("services.data_processing")
    data_processing_pkg.__path__ = []
    core_pkg = types.ModuleType("services.data_processing.core")
    core_pkg.__path__ = []

    safe_import("services", services_pkg)
    safe_import("services.data_processing", data_processing_pkg)
    safe_import("services.data_processing.core", core_pkg)
    monkeypatch.setitem(
        sys.modules,
        "core.protocols.plugin",
        protocols,
    )


def test_thread_stops_after_atexit(monkeypatch):
    _install_protocol_stubs(monkeypatch)

    handlers = []

    def fake_register(func):
        handlers.append(func)
        return func

    monkeypatch.setattr(atexit, "register", fake_register)

    from yosai_intel_dashboard.src.core.plugins.manager import (
        ThreadSafePluginManager as PluginManager,
    )

    mgr = PluginManager(
        ServiceContainer(), create_config_manager(), health_check_interval=1
    )
    assert mgr._health_thread.is_alive()

    for func in handlers:
        func()

    time.sleep(0.1)
    assert not mgr._health_thread.is_alive()
