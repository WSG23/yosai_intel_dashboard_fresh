import logging
import os
from typing import Any, Awaitable, MutableMapping

import structlog
from opentelemetry import context as ot_context
from opentelemetry import propagate, trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_current_span

from .config import (
    DEFAULT_JAEGER_ENDPOINT,
    DEFAULT_TRACING_EXPORTER,
    DEFAULT_ZIPKIN_ENDPOINT,
    JAEGER_ENDPOINT_ENV,
    TRACING_EXPORTER_ENV,
    ZIPKIN_ENDPOINT_ENV,
)


def init_tracing(service_name: str) -> None:
    exporter_type = os.getenv(TRACING_EXPORTER_ENV, DEFAULT_TRACING_EXPORTER).lower()
    if exporter_type == "zipkin":
        endpoint = os.getenv(ZIPKIN_ENDPOINT_ENV, DEFAULT_ZIPKIN_ENDPOINT)
        exporter = ZipkinExporter(endpoint=endpoint)
    else:
        endpoint = os.getenv(JAEGER_ENDPOINT_ENV, DEFAULT_JAEGER_ENDPOINT)
        exporter = JaegerExporter(collector_endpoint=endpoint)

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def _add_trace_ids(_: structlog.BoundLogger, __: str, event_dict: dict) -> dict:
    span = get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        event_dict["trace_id"] = f"{ctx.trace_id:032x}"
        event_dict["span_id"] = f"{ctx.span_id:016x}"
    return event_dict


def configure_logging(
    service_name: str,
    version: str | None = None,
    environment: str | None = None,
) -> None:
    """Setup structured logging with service metadata."""
    version = version or os.getenv("SERVICE_VERSION", "0.0.0")
    environment = environment or os.getenv("APP_ENV", "development")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _add_trace_ids,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.get_logger().bind(
        service=service_name, service_version=version, environment=environment
    )


async def trace_async_operation(name: str, task_id: str, coro: Awaitable[Any]) -> Any:
    """Run *coro* in a new span for background tasks."""
    tracer = trace.get_tracer("async-operations")
    token = ot_context.attach(ot_context.get_current())
    try:
        with tracer.start_as_current_span(
            name, attributes={"task.id": task_id}
        ) as span:
            return await coro
    except Exception as exc:  # pragma: no cover - error handling
        span.record_exception(exc)
        raise
    finally:
        ot_context.detach(token)


def propagate_context(headers: MutableMapping[str, str]) -> None:
    """Inject the current trace context into HTTP *headers*."""
    propagate.inject(headers)
