from prometheus_client import Counter

serialization_errors_total = Counter(
    "kafka_serialization_errors_total",
    "Total Avro serialization errors",
)

deserialization_errors_total = Counter(
    "kafka_deserialization_errors_total",
    "Total Avro deserialization errors",
)

__all__ = ["serialization_errors_total", "deserialization_errors_total"]
