"""Simple registry for optional services and service discovery."""

from __future__ import annotations

import asyncio
import logging
import os
from importlib import import_module
from typing import Any, Dict, Optional

import aiohttp

try:  # pragma: no cover - tracing optional
    from tracing import propagate_context
except Exception:  # pragma: no cover - fallback when tracing unavailable
    def propagate_context(_: Dict[str, str]) -> None:  # type: ignore[override]
        return None

from yosai_intel_dashboard.src.core.async_utils.async_circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
)
from yosai_intel_dashboard.src.error_handling.core import ErrorHandler
from yosai_intel_dashboard.src.error_handling.exceptions import ErrorCategory
from yosai_intel_dashboard.src.services.base_database_service import BaseDatabaseService

logger = logging.getLogger(__name__)


class ServiceRegistry(BaseDatabaseService):
    """Registry mapping service names to import paths."""

    def __init__(self) -> None:
        super().__init__(None)
        self._services: Dict[str, str] = {}

    def register_service(self, name: str, import_path: str) -> None:
        """Register a service by import path.

        ``import_path`` may include an attribute name using the ``module:attr`` syntax.
        """
        self._services[name] = import_path

    def get_service(self, name: str) -> Optional[Any]:
        """Return the resolved service or ``None`` if not available."""
        path = self._services.get(name)
        if not path:
            return None
        module_path, _, attr = path.partition(":")
        try:
            module = import_module(module_path)
        except ImportError as exc:  # pragma: no cover - optional dependency
            logger.warning("Optional service '%s' unavailable: %s", name, exc)
            return None
        return getattr(module, attr) if attr else module

# Backwards compatibility: provide module-level ``registry`` alias so external
# code can import ``from ...core import ServiceRegistry, registry`` and continue
# using ``registry.register(...)`` style APIs.
registry = ServiceRegistry

__all__ = ["ServiceRegistry", "registry"]
