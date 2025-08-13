"""Telemetry configuration for analytics services."""

import os
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from tracing.config import (
    DEFAULT_JAEGER_ENDPOINT,
    DEFAULT_TRACING_EXPORTER,
    DEFAULT_ZIPKIN_ENDPOINT,
    JAEGER_ENDPOINT_ENV,
    TRACING_EXPORTER_ENV,
    ZIPKIN_ENDPOINT_ENV,
)


def configure_tracing(service_name: str) -> None:
    """Configure OpenTelemetry with the repository's tracing backend."""
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
