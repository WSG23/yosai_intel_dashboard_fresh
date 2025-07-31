"""Prometheus metrics for data quality issues."""

from prometheus_client import REGISTRY, Counter
from prometheus_client.core import CollectorRegistry

if "avro_decoding_failures_total" not in REGISTRY._names_to_collectors:
    avro_decoding_failures = Counter(
        "avro_decoding_failures_total", "Count of Avro decoding failures"
    )
    compatibility_failures = Counter(
        "schema_compatibility_failures_total",
        "Count of schema compatibility check failures",
    )
else:  # pragma: no cover - defensive in tests
    avro_decoding_failures = Counter(
        "avro_decoding_failures_total",
        "Count of Avro decoding failures",
        registry=CollectorRegistry(),
    )
    compatibility_failures = Counter(
        "schema_compatibility_failures_total",
        "Count of schema compatibility check failures",
        registry=CollectorRegistry(),
    )

__all__ = ["avro_decoding_failures", "compatibility_failures"]
