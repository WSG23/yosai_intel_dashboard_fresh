import logging
import os
import signal
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Histogram,
    start_http_server,
)

from yosai_intel_dashboard.src.error_handling import http_error
from shared.errors.types import ErrorCode

from .config import ServiceConfig, load_config
from tracing.config import DEFAULT_JAEGER_ENDPOINT, DEFAULT_ZIPKIN_ENDPOINT


class BaseService:
    """Basic service with logging, metrics, tracing and signal handling."""

    def __init__(self, name: str, config_path: str):
        self.name = name
        self.config: ServiceConfig = load_config(config_path)
        self.log = logging.getLogger(name)
        self.running = False
        self.app = FastAPI(title=name)
        self.app.state.ready = False
        self.app.state.live = True
        self.app.state.startup_complete = False
        self._add_health_routes()

    def start(self) -> None:
        self._setup_logging()
        self._setup_metrics()
        self._setup_tracing()
        self._setup_signals()
        if self.config.enable_profiling:
            from .profiling_middleware import ProfilingMiddleware

            self.app.add_middleware(ProfilingMiddleware, service=self)
        self.running = True
        self.app.state.startup_complete = True
        self.app.state.ready = True
        self.log.info("service %s started", self.name)

    # ------------------------------------------------------------------
    def stop(self, *_: Any) -> None:
        if self.running:
            self.running = False
            self.app.state.ready = False
            self.app.state.live = False
            self.log.info("service %s stopping", self.name)
            # Flush metrics and tracing data
            try:
                list(REGISTRY.collect())
            except Exception:  # pragma: no cover - best effort
                pass
            try:
                provider = trace.get_tracer_provider()
                if hasattr(provider, "shutdown"):
                    provider.shutdown()
            except Exception:  # pragma: no cover - best effort
                pass

    # ------------------------------------------------------------------
    def _setup_logging(self) -> None:
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(level=level, format="%(message)s")
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            logger_factory=structlog.stdlib.LoggerFactory(),
        )
        self.log = structlog.get_logger(self.name)

    def _setup_metrics(self) -> None:
        """Register Prometheus metrics and expose HTTP endpoint."""
        if "yosai_request_total" not in REGISTRY._names_to_collectors:
            self.request_total = Counter(
                "yosai_request_total", "Total requests handled"
            )
        else:  # pragma: no cover - defensive
            self.request_total = Counter(
                "yosai_request_total",
                "Total requests handled",
                registry=CollectorRegistry(),
            )

        if "yosai_request_duration_seconds" not in REGISTRY._names_to_collectors:
            self.request_duration = Histogram(
                "yosai_request_duration_seconds", "Request duration"
            )
        else:  # pragma: no cover - defensive
            self.request_duration = Histogram(
                "yosai_request_duration_seconds",
                "Request duration",
                registry=CollectorRegistry(),
            )

        if "yosai_error_total" not in REGISTRY._names_to_collectors:
            self.error_total = Counter("yosai_error_total", "Total errors encountered")
        else:  # pragma: no cover - defensive
            self.error_total = Counter(
                "yosai_error_total",
                "Total errors encountered",
                registry=CollectorRegistry(),
            )

        if "yosai_request_memory_mb" not in REGISTRY._names_to_collectors:
            self.request_memory = Histogram(
                "yosai_request_memory_mb", "Change in memory usage during request"
            )
        else:  # pragma: no cover - defensive
            self.request_memory = Histogram(
                "yosai_request_memory_mb",
                "Change in memory usage during request",
                registry=CollectorRegistry(),
            )

        if self.config.metrics_addr:
            host, port_str = self.config.metrics_addr.rsplit(":", 1)
            start_http_server(int(port_str), addr=host or "0.0.0.0")

    def _setup_tracing(self) -> None:
        """Initialize OpenTelemetry tracing exported to Jaeger or Zipkin."""
        exporter_type = os.getenv("TRACING_EXPORTER", self.config.tracing_exporter).lower()
        if exporter_type == "zipkin":
            endpoint = self.config.tracing_endpoint or DEFAULT_ZIPKIN_ENDPOINT
            exporter = ZipkinExporter(endpoint=endpoint)
        else:
            endpoint = self.config.tracing_endpoint or DEFAULT_JAEGER_ENDPOINT
            exporter = JaegerExporter(collector_endpoint=endpoint)
        provider = TracerProvider(resource=Resource.create({"service.name": self.name}))
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

    def _setup_signals(self) -> None:
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

    # ------------------------------------------------------------------
    def _add_health_routes(self) -> None:
        from yosai_intel_dashboard.src.core.app_factory.health import (
            check_critical_dependencies,
        )

        @self.app.get("/health")
        async def _health() -> dict[str, str]:
            healthy, reason = check_critical_dependencies()
            if healthy:
                return {"status": "healthy"}
            return JSONResponse(
                {"status": "unhealthy", "reason": reason}, status_code=503
            )

        @self.app.get("/health/live")
        async def _health_live() -> dict[str, str]:
            return {"status": "ok" if self.app.state.live else "shutdown"}

        @self.app.get("/health/ready")
        async def _health_ready() -> dict[str, str]:
            if self.app.state.ready:
                return {"status": "ready"}
            raise http_error(ErrorCode.UNAVAILABLE, "not ready", 503)

        @self.app.get("/health/startup")
        async def _health_startup() -> dict[str, str]:
            if self.app.state.startup_complete:
                return {"status": "complete"}
            raise http_error(ErrorCode.UNAVAILABLE, "starting", 503)
