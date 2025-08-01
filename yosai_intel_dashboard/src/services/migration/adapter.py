"""Adapters for gradually migrating the monolith to microservices."""

from __future__ import annotations

import asyncio
import json
import os
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import aiohttp
import pandas as pd
from kafka import KafkaProducer

logger = logging.getLogger(__name__)

from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from yosai_intel_dashboard.src.services.feature_flags import feature_flags
from yosai_intel_dashboard.src.core.interfaces.service_protocols import AnalyticsServiceProtocol
from yosai_intel_dashboard.src.core.async_utils.async_circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
)

# Namespace for Kubernetes DNS lookups
K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "yosai-dev")


def k8s_service_url(name: str) -> str:
    """Return http base URL for *name* service via cluster DNS."""
    return f"http://{name}.{K8S_NAMESPACE}.svc.cluster.local"


class ServiceAdapter(ABC):
    """Base adapter for migrating services to microservices."""

    @abstractmethod
    async def call(self, method: str, **kwargs: Any) -> Any:
        """Invoke *method* with *kwargs* on the underlying service."""
        pass


class EventServiceAdapter(ServiceAdapter):
    """Adapter for the Go event ingestion service."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or os.getenv(
            "EVENT_SERVICE_URL", "http://localhost:8002"
        )
        self.kafka_producer: KafkaProducer | None = None
        self.circuit_breaker = CircuitBreaker(5, 60, name="event_service")
        self._init_kafka()

    def _init_kafka(self) -> None:
        """Initialize Kafka producer if brokers are available."""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
        except Exception as exc:  # pragma: no cover - runtime setup
            logger.warning("Kafka initialization failed, using HTTP fallback: %s", exc)
            self.kafka_producer = None

    async def call(self, method: str, **kwargs: Any) -> Any:
        if method == "process_event":
            return await self._process_event(kwargs.get("event"))
        if method == "process_batch":
            return await self._process_batch(kwargs.get("events"))
        raise ValueError(f"Unknown method: {method}")

    async def _process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Send a single event via Kafka or HTTP."""
        if self.kafka_producer is not None:
            try:
                async with self.circuit_breaker:
                    future = self.kafka_producer.send(
                        "access-events",
                        key=event.get("event_id"),
                        value=event,
                    )
                    future.get(timeout=0.05)
                    return {
                        "event_id": event.get("event_id"),
                        "status": "accepted",
                        "method": "kafka",
                    }
            except CircuitBreakerOpen:
                logger.warning("Event service circuit open, skipping Kafka")
            except Exception as exc:  # pragma: no cover - network failures
                logger.warning("Kafka send failed, falling back to HTTP: %s", exc)

        try:
            async with self.circuit_breaker:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/v1/events",
                        json=event,
                        timeout=aiohttp.ClientTimeout(total=0.1),
                    ) as response:
                        return await response.json()
        except CircuitBreakerOpen:
            return {"event_id": event.get("event_id"), "status": "unavailable"}

    async def _process_batch(
        self, events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Send a batch of events via HTTP."""
        try:
            async with self.circuit_breaker:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/v1/events/batch",
                        json={"events": events},
                        timeout=aiohttp.ClientTimeout(total=1.0),
                    ) as response:
                        return await response.json()
        except CircuitBreakerOpen:
            return []


class AnalyticsServiceAdapter(ServiceAdapter, AnalyticsServiceProtocol):
    """Adapter for routing analytics calls to a microservice with fallback."""

    def __init__(
        self, python_service: Any, microservice_url: str | None = None
    ) -> None:
        self.python_service = python_service
        self.microservice_url = microservice_url or os.getenv(
            "ANALYTICS_SERVICE_URL", "http://localhost:8001"
        )
        self.use_microservice = feature_flags.is_enabled("use_analytics_microservice")
        self.circuit_breaker = CircuitBreaker(5, 60, name="analytics_service")

    async def call(self, method: str, **kwargs: Any) -> Any:
        if not self.use_microservice:
            python_method = getattr(self.python_service, method)
            result = python_method(**kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result

        try:
            return await self._call_microservice(method, kwargs)
        except Exception as exc:
            raise RuntimeError(f"Analytics microservice call failed: {exc}") from exc

    async def _call_microservice(self, method: str, params: Dict[str, Any]) -> Any:
        async with self.circuit_breaker:
            async with aiohttp.ClientSession() as session:
                if method == "get_dashboard_summary":
                    async with session.get(
                        f"{self.microservice_url}/v1/analytics/dashboard-summary",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30.0),
                    ) as response:
                        return await response.json()
                elif method == "get_access_patterns_analysis":
                    async with session.get(
                        f"{self.microservice_url}/v1/analytics/access-patterns",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30.0),
                    ) as response:
                        return await response.json()
                else:
                    async with session.post(
                        f"{self.microservice_url}/v1/analytics/{method}",
                        json=params,
                        timeout=aiohttp.ClientTimeout(total=30.0),
                    ) as response:
                        return await response.json()

    # ``AnalyticsServiceProtocol`` methods ---------------------------------
    async def get_dashboard_summary_async(self) -> Dict[str, Any]:
        return await self.call("get_dashboard_summary")

    def get_dashboard_summary(self) -> Dict[str, Any]:
        return asyncio.run(self.get_dashboard_summary_async())

    async def get_access_patterns_analysis_async(self, days: int = 7) -> Dict[str, Any]:
        return await self.call("get_access_patterns_analysis", days=days)

    def get_access_patterns_analysis(self, days: int = 7) -> Dict[str, Any]:
        return asyncio.run(self.get_access_patterns_analysis_async(days))

    def process_dataframe(
        self, df: pd.DataFrame
    ) -> Dict[str, Any]:  # pragma: no cover - passthrough
        return self.python_service.process_dataframe(df)


class MigrationContainer(ServiceContainer):
    """Service container with migration feature flags and adapters."""

    def __init__(self) -> None:
        super().__init__()
        self._adapters: Dict[str, ServiceAdapter] = {}
        self._migration_flags = self._load_migration_flags()

    def _load_migration_flags(self) -> Dict[str, bool]:
        return {
            "use_kafka_events": feature_flags.is_enabled("use_kafka_events"),
            "use_timescaledb": feature_flags.is_enabled("use_timescaledb"),
        }

    def register_with_adapter(
        self, name: str, python_service: Any, adapter: ServiceAdapter
    ) -> None:
        self._adapters[name] = adapter
        self.register_singleton(name, adapter)

    def get_migration_status(self) -> Dict[str, Any]:
        return {
            "flags": self._migration_flags,
            "services": {
                name: {
                    "using_microservice": isinstance(self.get(name), ServiceAdapter),
                    "adapter_type": (
                        type(self._adapters.get(name)).__name__
                        if name in self._adapters
                        else None
                    ),
                }
                for name in self._services
            },
        }


def register_migration_services(container: MigrationContainer) -> None:
    """Register services with their migration adapters using cluster DNS."""

    event_adapter = EventServiceAdapter(base_url=k8s_service_url("events"))
    container.register_with_adapter("event_processor", None, event_adapter)

    from yosai_intel_dashboard.src.services.analytics.analytics_service import create_analytics_service

    python_analytics = create_analytics_service()
    analytics_adapter = AnalyticsServiceAdapter(
        python_analytics, microservice_url=k8s_service_url("analytics")
    )
    container.register_with_adapter(
        "analytics_service",
        python_analytics,
        analytics_adapter,
    )

    if container._migration_flags["use_timescaledb"]:
        try:
            from yosai_intel_dashboard.src.services.timescale import models as timescale_models  # noqa:F401
            from yosai_intel_dashboard.src.services.timescale.manager import TimescaleDBManager
        except Exception:  # pragma: no cover - optional dependency
            pass
        else:
            container.register_factory("database", TimescaleDBManager)
