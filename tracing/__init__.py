import os
from opentelemetry import trace
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
