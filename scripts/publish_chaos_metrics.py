#!/usr/bin/env python3
"""Publish chaos experiment metrics to Prometheus Pushgateway."""
from __future__ import annotations

import json
import os
import sys

from prometheus_client import CollectorRegistry, Counter, Histogram, push_to_gateway

PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "http://localhost:9091")


def main() -> None:
    data = json.load(sys.stdin)
    registry = CollectorRegistry()
    recovery = Histogram(
        "chaos_experiment_recovery_seconds",
        "Service recovery time after chaos experiment",
        ["experiment"],
        registry=registry,
    )
    failures = Counter(
        "chaos_experiment_failed_total",
        "Number of failed chaos experiments",
        ["experiment"],
        registry=registry,
    )

    recovery.labels(data["name"]).observe(float(data["duration"]))
    if not data.get("succeeded", True):
        failures.labels(data["name"]).inc()

    push_to_gateway(PUSHGATEWAY_URL, job="chaos-tests", registry=registry)
    print("Published chaos metrics")


if __name__ == "__main__":
    main()
