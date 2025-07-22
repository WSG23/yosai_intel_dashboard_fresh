import os
from typing import Any, Awaitable, MutableMapping

from opentelemetry import context as ot_context, propagate, trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .config import JAEGER_ENDPOINT_ENV, DEFAULT_JAEGER_ENDPOINT


def init_tracing(service_name: str) -> None:
    endpoint = os.getenv(JAEGER_ENDPOINT_ENV, DEFAULT_JAEGER_ENDPOINT)
    exporter = JaegerExporter(collector_endpoint=endpoint)
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


async def trace_async_operation(name: str, task_id: str, coro: Awaitable[Any]) -> Any:
    """Run *coro* in a new span for background tasks."""
    tracer = trace.get_tracer("async-operations")
    token = ot_context.attach(ot_context.get_current())
    try:
        with tracer.start_as_current_span(name, attributes={"task.id": task_id}) as span:
            return await coro
    except Exception as exc:  # pragma: no cover - error handling
        span.record_exception(exc)
        raise
    finally:
        ot_context.detach(token)


def propagate_context(headers: MutableMapping[str, str]) -> None:
    """Inject the current trace context into HTTP *headers*."""
    propagate.inject(headers)
