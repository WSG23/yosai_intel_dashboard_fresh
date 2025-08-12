"""Deprecated alias for :mod:`core.registry`."""

from __future__ import annotations

from warnings import warn

warn(
    "services.registry is deprecated; use core.registry instead", 
    DeprecationWarning,
    stacklevel=2,
)

from yosai_intel_dashboard.src.core.registry import (
    ServiceDiscovery,
    ServiceRegistry,
    get_service,
    register_builtin_services,
    register_service,
    registry,
)

__all__ = [
    "ServiceRegistry",
    "ServiceDiscovery",
    "registry",
    "register_service",
    "get_service",
    "register_builtin_services",
]
