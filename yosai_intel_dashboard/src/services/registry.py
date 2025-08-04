"""Simple registry for optional services."""

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

from .base_database_service import BaseDatabaseService
from yosai_intel_dashboard.src.error_handling import ErrorCategory, ErrorHandler

logger = logging.getLogger(__name__)


class ServiceRegistry(BaseDatabaseService):
    """Registry mapping service names to import paths."""

    def __init__(self) -> None:
        super().__init__(None)
        self._services: Dict[str, str] = {}

    def register_service(self, name: str, import_path: str) -> None:
        """Register a service by import path.

        ``import_path`` may include an attribute name using the ``module:attr``
        syntax.
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


class ServiceDiscovery:
    """Client for fetching microservice addresses from Consul-like registry."""

    def __init__(self, base_url: str | None = None) -> None:
        url = (
            base_url
            or os.getenv("SERVICE_REGISTRY_URL")
            or os.getenv("CONSUL_ADDR", "http://localhost:8500")
        )
        self.base_url = url.rstrip("/")
        self.session = aiohttp.ClientSession()
        self._circuit_breaker = CircuitBreaker(5, 30, name="service_discovery")
        self._error_handler = ErrorHandler()
        self._cache: Dict[str, str] = {}

    def _get_cached(self, name: str) -> Optional[str]:
        return self._cache.get(name)

    def _set_cached(self, name: str, value: str) -> None:
        self._cache[name] = value

    async def resolve_async(self, name: str) -> Optional[str]:
        """Return ``host:port`` for *name* or ``None`` if lookup fails."""
        cached = self._get_cached(name)
        if cached is not None:
            return cached
        try:
            headers: Dict[str, str] = {}
            propagate_context(headers)
            async with self._circuit_breaker:
                async with self.session.get(
                    f"{self.base_url}/v1/health/service/{name}",
                    params={"passing": 1},
                    headers=headers,
                    timeout=2,
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if not data:
                        return None
                    svc = data[0]["Service"]
                    addr = f"{svc['Address']}:{svc['Port']}"
                    self._set_cached(name, addr)
                    return addr
        except CircuitBreakerOpen as exc:  # pragma: no cover - circuit open
            self._error_handler.handle(exc, ErrorCategory.UNAVAILABLE)
            return None

        except Exception as exc:  # pragma: no cover - network failures
            self._error_handler.handle(exc, ErrorCategory.UNAVAILABLE)
            cached = self._get_cached(name)
            if cached is not None:
                return cached
            env = os.getenv(f"{name.upper()}_SERVICE_URL")
            return env

    def resolve(self, name: str) -> Optional[str]:
        """Return ``host:port`` for *name* or ``None`` if lookup fails."""
        return asyncio.run(self.resolve_async(name))


# Global registry instance
registry = ServiceRegistry()

# Convenience wrappers
register_service = registry.register_service
get_service = registry.get_service



# Built-in optional services registration -------------------------------------------------
def register_builtin_services() -> None:
    """Register optional services provided by the main application."""

    register_service(
        "FileProcessor",
        "services.data_processing.file_handler:FileHandler",
    )
    register_service(
        "FileHandler",
        "services.data_processing.file_handler:FileHandler",
    )
    register_service(
        "SecurityValidator",
        "validation.security_validator:SecurityValidator",
    )
    register_service("UploadAnalyticsProcessor", "services.upload_processing:UploadAnalyticsProcessor")

    register_service(
        "AsyncFileProcessor", "services.async_file_processor:AsyncFileProcessor"
    )

    register_service(
        "get_analytics_service",
        "services.analytics_service:get_analytics_service",
    )
    register_service(
        "create_analytics_service",
        "services.analytics_service:create_analytics_service",
    )
    register_service(
        "AnalyticsService",
        "services.analytics_service:AnalyticsService",
    )

    # Optional model and database classes
    register_service("BaseModel", "models.base:BaseModel")
    register_service("AccessEventModel", "models.base:AccessEventModel")
    register_service("AnomalyDetectionModel", "models.base:AnomalyDetectionModel")
    register_service("ModelFactory", "models.base:ModelFactory")
    register_service(
        "DatabaseConnectionFactory",
        "config.database_manager:DatabaseConnectionFactory",
    )


__all__ = [
    "ServiceRegistry",
    "ServiceDiscovery",
    "registry",
    "register_service",
    "get_service",
    "register_builtin_services",
]
