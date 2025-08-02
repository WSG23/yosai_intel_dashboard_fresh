#!/usr/bin/env python3
from __future__ import annotations

"""Validate Locust metrics against threshold targets."""

import csv
import json
import sys
from pathlib import Path


def load_metrics(csv_path: str):
    metrics = {}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Name"]
            if name == "Aggregated":
                continue
            metrics[name] = {
                "p50": float(row["50%"]),
                "p95": float(row["95%"]),
                "p99": float(row["99%"]),
            }
    return metrics


def main(csv_path: str, thresholds_path: str) -> int:
    metrics = load_metrics(csv_path)
    thresholds = json.load(open(thresholds_path)).get("endpoints", {})

    for ep, limits in thresholds.items():
        if ep not in metrics:
            print(f"warning: no data for endpoint {ep}", file=sys.stderr)
            continue
        for key in ["p50", "p95", "p99"]:
            value = metrics[ep][key]
            target = limits[key]
            if value > target:
                raise SystemExit(f"{ep} {key} {value} exceeds threshold {target}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: validate_thresholds.py <csv_metrics> <thresholds.json>")
        raise SystemExit(1)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
