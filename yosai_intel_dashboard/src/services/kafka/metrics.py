from prometheus_client import Counter

serialization_errors_total = Counter(
    "kafka_serialization_errors_total",
    "Total Avro serialization errors",
)

deserialization_errors_total = Counter(
    "kafka_deserialization_errors_total",
    "Total Avro deserialization errors",
)

delivery_success_total = Counter(
    "kafka_delivery_success_total",
    "Total successfully delivered Kafka messages",
)

delivery_failure_total = Counter(
    "kafka_delivery_failure_total",
    "Total Kafka messages that failed delivery",
)
__all__ = [
    "serialization_errors_total",
    "deserialization_errors_total",
    "delivery_success_total",
    "delivery_failure_total",
]
