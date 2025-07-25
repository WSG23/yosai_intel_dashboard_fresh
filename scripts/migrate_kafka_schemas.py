#!/usr/bin/env python3
"""Migrate Kafka Avro schemas and optionally reprocess topics."""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Iterable

import requests

from yosai_intel_dashboard.src.services.kafka.avro_consumer import AvroConsumer
from yosai_intel_dashboard.src.services.kafka.avro_producer import AvroProducer

SCHEMA_MAP = {
    "schemas/avro/access_event_v1.avsc": [
        "access-events-value",
        "access-events-enriched-value",
    ],
    "schemas/avro/analytics_event_v1.avsc": ["analytics-events-value"],
    "schemas/avro/anomaly_event_v1.avsc": ["anomaly-events-value"],
}


def fetch_current_versions(registry_url: str, subjects: Iterable[str]) -> None:
    """Print current schema versions for ``subjects``."""
    for sub in subjects:
        try:
            resp = requests.get(
                f"{registry_url}/subjects/{sub}/versions/latest", timeout=5
            )
            if resp.status_code == 404:
                logging.info("Subject %s not found", sub)
                continue
            resp.raise_for_status()
            data = resp.json()
            logging.info("%s latest version %s", sub, data.get("version"))
        except Exception as exc:  # pragma: no cover - best effort
            logging.error("Failed to fetch version for %s: %s", sub, exc)


def register_new_version(
    registry_url: str, subject: str, schema_path: Path, dry_run: bool
) -> None:
    schema_text = schema_path.read_text(encoding="utf-8")
    payload = {"schema": schema_text}
    if dry_run:
        logging.info("Would register %s for %s", schema_path, subject)
        return
    try:
        resp = requests.post(
            f"{registry_url}/subjects/{subject}/versions",
            headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
            json=payload,
            timeout=5,
        )
        resp.raise_for_status()
        logging.info("Registered %s version %s", subject, resp.json().get("id"))
    except Exception as exc:  # pragma: no cover - best effort
        logging.error("Failed to register schema for %s: %s", subject, exc)


def reprocess_topic(
    topic: str,
    subject: str,
    brokers: str,
    registry: str,
    dry_run: bool,
) -> None:
    consumer = AvroConsumer(
        [topic],
        brokers=brokers,
        group_id="schema-migrator",
        schema_registry=registry,
    )
    producer = AvroProducer(brokers=brokers, schema_registry=registry)
    count = 0
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                break
            value = getattr(msg, "decoded", None)
            if value is None:
                continue
            if dry_run:
                logging.info(
                    "Would reprocess message at offset %s from %s",
                    msg.offset(),
                    topic,
                )
            else:
                producer.produce(topic, value, subject, key=msg.key())
                count += 1
    finally:
        producer.flush()
        consumer.close()
    if not dry_run:
        logging.info("Reprocessed %s messages from %s", count, topic)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate Kafka Avro schemas")
    parser.add_argument(
        "--schema-registry",
        default=os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081"),
        help="Schema Registry URL",
    )
    parser.add_argument(
        "--brokers",
        default=os.getenv("KAFKA_BROKERS", "localhost:9092"),
        help="Kafka bootstrap servers",
    )
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="Reprocess existing topics after registering schemas",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without executing",
    )

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    subjects = [s for subs in SCHEMA_MAP.values() for s in subs]
    fetch_current_versions(args.schema_registry, subjects)

    for path_str, subs in SCHEMA_MAP.items():
        path = Path(path_str)
        if not path.is_file():
            logging.warning("Schema file missing: %s", path)
            continue
        for sub in subs:
            register_new_version(args.schema_registry, sub, path, args.dry_run)

    if args.reprocess:
        for path_str, subs in SCHEMA_MAP.items():
            topic = sub_to_topic(subs[0]) if subs else None
            if not topic:
                continue
            for sub in subs:
                reprocess_topic(
                    topic, sub, args.brokers, args.schema_registry, args.dry_run
                )

    return 0


def sub_to_topic(subject: str) -> str | None:
    if subject.endswith("-value"):
        return subject[:-6]
    return None


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
