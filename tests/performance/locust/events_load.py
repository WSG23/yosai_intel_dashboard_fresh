"""Locust tasks for event ingestion throughput testing."""

import json

from locust import HttpUser, between, task

from .utils import generate_event


class EventIngestionUser(HttpUser):
    """Simulate users sending events via REST and Kafka."""

    wait_time = between(0.001, 0.005)

    def on_start(self) -> None:
        """Initialize optional Kafka producer if available."""
        try:
            from confluent_kafka import Producer

            self.producer = Producer({"bootstrap.servers": "localhost:9092"})
        except Exception:  # pragma: no cover - optional dependency
            self.producer = None

    @task(2)
    def rest_event(self) -> None:
        """Send event to the REST API."""
        event = generate_event()
        self.client.post("/events", json=event, name="REST /events")

    @task(1)
    def kafka_event(self) -> None:
        """Publish event to Kafka topic if producer available."""
        if not self.producer:
            return
        event = generate_event()
        self.producer.produce(
            "events", key=event["user_id"], value=json.dumps(event).encode()
        )
        self.producer.poll(0)
