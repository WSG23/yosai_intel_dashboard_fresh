import os
from dataclasses import dataclass, field


@dataclass
class KafkaConfig:
    """Configuration for Kafka connection."""

    brokers: str = field(
        default_factory=lambda: os.getenv("KAFKA_BROKERS", "localhost:9092")
    )
    schema_registry_url: str = field(
        default_factory=lambda: os.getenv(
            "SCHEMA_REGISTRY_URL", "http://localhost:8081"
        )
    )


def from_environment() -> KafkaConfig:
    """Create :class:`KafkaConfig` using environment variables."""
    return KafkaConfig(
        brokers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
        schema_registry_url=os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081"),
    )


__all__ = ["KafkaConfig", "from_environment"]
