#!/usr/bin/env python3
from __future__ import annotations

"""Generate JSON and HTML regression reports from Locust stats."""

import csv
import json
import pathlib
import sys
from typing import Dict


def load_current(csv_path: str) -> Dict[str, Dict[str, float]]:
    stats = {}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Name"]
            if name == "Aggregated":
                continue
            stats[name] = {
                "throughput": float(row["Requests/s"]),
                "p50": float(row["50%"]),
                "p95": float(row["95%"]),
                "p99": float(row["99%"]),
            }
    return stats


def compare(
    current: Dict[str, Dict[str, float]], baseline: Dict[str, Dict[str, float]]
):
    report = {}
    for ep, cur in current.items():
        base = baseline.get(ep, {})
        report[ep] = {}
        for metric in ["throughput", "p50", "p95", "p99"]:
            report[ep][metric] = {
                "current": cur.get(metric),
                "baseline": base.get(metric),
                "delta": cur.get(metric) - base.get(metric, 0),
            }
    return report


def write_html(
    report: Dict[str, Dict[str, Dict[str, float]]], out_file: pathlib.Path
) -> None:
    with out_file.open("w") as f:
        f.write("<html><body><table border='1'>")
        f.write(
            "<tr><th>Endpoint</th><th>Metric</th><th>Current</th><th>Baseline</th><th>Delta</th></tr>"
        )
        for ep, metrics in report.items():
            for metric, values in metrics.items():
                f.write(
                    f"<tr><td>{ep}</td><td>{metric}</td><td>{values['current']}</td><td>{values['baseline']}</td><td>{values['delta']}</td></tr>"
                )
        f.write("</table></body></html>")


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: generate_report.py <current_csv> <baseline_json> <output_dir>")
        return 1

    csv_path, baseline_path, out_dir = sys.argv[1:]
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    current = load_current(csv_path)
    baseline = {}
    if pathlib.Path(baseline_path).exists():
        with open(baseline_path) as f:
            baseline = json.load(f)

    report = compare(current, baseline)

    with open(out_dir / "regression_report.json", "w") as f:
        json.dump(report, f, indent=2)

    write_html(report, out_dir / "regression_report.html")
    print(f"Regression report written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
