#!/usr/bin/env python3
"""Simple Kafka load test script."""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests
from kafka import KafkaProducer

# ensure project modules can be imported when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROM_QUERY_ENDPOINT = "/api/v1/query"


def query_prometheus(base_url: str, query: str) -> float:
    """Return the current value for a Prometheus query."""
    try:
        resp = requests.get(
            f"{base_url}{PROM_QUERY_ENDPOINT}",
            params={"query": query},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data["data"]["result"][0]["value"][1])
    except Exception:
        return 0.0


def produce_events(brokers: str, rate: float, duration: int) -> int:
    """Publish synthetic access events to Kafka."""
    producer = KafkaProducer(
        bootstrap_servers=brokers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    interval = 1.0 / rate if rate > 0 else 0.0
    end_time = time.time() + duration
    sent = 0
    while time.time() < end_time:
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "person_id": f"p{sent % 1000}",
            "door_id": f"d{sent % 100}",
            "access_result": "Granted",
        }
        producer.send("access-events", event)
        sent += 1
        if interval:
            time.sleep(interval)
    producer.flush()
    return sent


def run_test(brokers: str, prom_url: str, rate: float, duration: int) -> None:
    start_count = query_prometheus(
        prom_url,
        "event_processor_events_processed_total",
    )
    start_time = time.time()
    sent = produce_events(brokers, rate, duration)
    # wait until all events processed or timeout
    deadline = time.time() + 30
    processed = 0.0
    while time.time() < deadline:
        processed = query_prometheus(
            prom_url,
            "event_processor_events_processed_total",
        ) - start_count
        if processed >= sent:
            break
        time.sleep(1)
    total_time = time.time() - start_time
    throughput = processed / total_time if total_time > 0 else 0.0
    results = {
        "events_sent": sent,
        "events_processed": processed,
        "throughput_eps": throughput,
        "test_duration_sec": total_time,
    }
    print(json.dumps(results, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish synthetic access events for load testing",
    )
    parser.add_argument(
        "--brokers",
        default="localhost:9092",
        help="Kafka bootstrap servers",
    )
    parser.add_argument(
        "--prom-url",
        default="http://localhost:9090",
        help="Prometheus base URL",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=50.0,
        help="Events per second",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in seconds",
    )
    args = parser.parse_args()
    run_test(args.brokers, args.prom_url, args.rate, args.duration)


if __name__ == "__main__":
    main()
