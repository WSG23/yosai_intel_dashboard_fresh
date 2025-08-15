"""Prometheus metrics for queue processing."""

from prometheus_client import REGISTRY, Counter
from prometheus_client.core import CollectorRegistry

if "queue_processed_messages_total" not in REGISTRY._names_to_collectors:
    processed_messages = Counter(
        "queue_processed_messages_total",
        "Number of messages processed successfully",
        ["queue"],
    )
else:  # pragma: no cover
    processed_messages = Counter(
        "queue_processed_messages_total",
        "Number of messages processed successfully",
        ["queue"],
        registry=CollectorRegistry(),
    )

if "queue_processing_errors_total" not in REGISTRY._names_to_collectors:
    processing_errors = Counter(
        "queue_processing_errors_total",
        "Number of errors while processing messages",
        ["queue"],
    )
else:  # pragma: no cover
    processing_errors = Counter(
        "queue_processing_errors_total",
        "Number of errors while processing messages",
        ["queue"],
        registry=CollectorRegistry(),
    )

__all__ = ["processed_messages", "processing_errors"]
