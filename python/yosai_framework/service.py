import logging
import signal
from typing import Any

import structlog
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import (
    Counter,
    Histogram,
    REGISTRY,
    start_http_server,
    CollectorRegistry,
)

from .config import ServiceConfig, load_config


class BaseService:
    """Basic service with logging, metrics, tracing and signal handling."""

    def __init__(self, name: str, config_path: str):
        self.name = name
        self.config: ServiceConfig = load_config(config_path)
        self.log = logging.getLogger(name)
        self.running = False

    def start(self) -> None:
        self._setup_logging()
        self._setup_metrics()
        self._setup_tracing()
        self._setup_signals()
        self.running = True
        self.log.info("service %s started", self.name)

    # ------------------------------------------------------------------
    def stop(self, *_: Any) -> None:
        if self.running:
            self.running = False
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
            self.error_total = Counter(
                "yosai_error_total", "Total errors encountered"
            )
        else:  # pragma: no cover - defensive
            self.error_total = Counter(
                "yosai_error_total",
                "Total errors encountered",
                registry=CollectorRegistry(),
            )

        if self.config.metrics_addr:
            host, port_str = self.config.metrics_addr.rsplit(":", 1)
            start_http_server(int(port_str), addr=host or "0.0.0.0")

    def _setup_tracing(self) -> None:
        """Initialize OpenTelemetry tracing exported to Jaeger."""
        endpoint = self.config.tracing_endpoint or "http://localhost:14268/api/traces"
        exporter = JaegerExporter(collector_endpoint=endpoint)
        provider = TracerProvider(
            resource=Resource.create({"service.name": self.name})
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

    def _setup_signals(self) -> None:
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)
