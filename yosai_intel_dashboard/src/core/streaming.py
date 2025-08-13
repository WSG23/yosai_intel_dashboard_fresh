"""Kafka consumer integration for incremental graph updates."""

from __future__ import annotations

from typing import Callable, Iterable, Optional

from .graph_etl_pipeline import GraphETLPipeline


class KafkaETLConsumer:
    """Consume access logs from Kafka and feed them into the ETL pipeline."""

    def __init__(
        self,
        config: dict,
        topics: Iterable[str],
        pipeline: GraphETLPipeline,
        consumer: Optional[object] = None,
    ) -> None:
        if consumer is None:
            from confluent_kafka import Consumer  # type: ignore

            consumer = Consumer(config)
        consumer.subscribe(list(topics))
        self.consumer = consumer
        self.pipeline = pipeline

    def run(
        self,
        handler: Callable[[dict], None],
        timeout: float = 1.0,
        max_messages: int | None = None,
    ) -> None:
        """Poll Kafka and process messages.

        ``handler`` is called with the snapshot returned by the pipeline for each
        message. ``max_messages`` can be used to limit the number of processed
        messages (useful for testing).
        """

        processed = 0
        while True:
            if max_messages is not None and processed >= max_messages:
                break
            message = self.consumer.poll(timeout)
            if message is None or getattr(message, "error", lambda: None)():
                continue
            log_line = message.value().decode("utf-8")
            snapshot = self.pipeline.process_logs([log_line])
            handler(snapshot)
            processed += 1


__all__ = ["KafkaETLConsumer"]

