#!/usr/bin/env python3
"""Generate comparative performance reports from load test outputs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Iterable, List

import yaml


def _metric_value(obj: Dict[str, Any], key: str) -> float:
    """Return metric value from k6 summary regardless of nesting."""
    if key in obj:
        return float(obj[key])
    values = obj.get("values")
    if isinstance(values, dict) and key in values:
        return float(values[key])
    return float("nan")


def parse_result(path: Path) -> Dict[str, float]:
    data = json.loads(path.read_text())
    metrics = data.get("metrics", {})
    failed = metrics.get("http_req_failed", {})
    duration = metrics.get("http_req_duration", {})
    return {
        "http_req_failed_rate": _metric_value(failed, "rate"),
        "http_req_duration_p95": _metric_value(duration, "p(95)"),
    }


def load_previous(report_dir: Path) -> Dict[str, float]:
    prev = report_dir / "latest.json"
    if prev.exists():
        return json.loads(prev.read_text())
    return {}


def alert_channels(alerts_file: Path) -> List[str]:
    if not alerts_file.exists():
        return []
    try:
        data = yaml.safe_load(alerts_file.read_text()) or {}
    except Exception:
        return []
    channels = set()
    for group in data.get("groups", []):
        for rule in group.get("rules", []):
            annotations = rule.get("annotations", {}) or {}
            ch = annotations.get("channels", [])
            if isinstance(ch, str):
                channels.add(ch)
            elif isinstance(ch, Iterable):
                channels.update(str(c) for c in ch)
    return sorted(channels)


def generate_table(current: Dict[str, float], previous: Dict[str, float]) -> str:
    lines = ["| Metric | Current | Previous | Change |", "|---|---|---|---|"]
    for metric, value in current.items():
        prev = previous.get(metric)
        if prev is None:
            prev_str = "N/A"
            change = "N/A"
        else:
            prev_str = f"{prev:.4f}"
            change = f"{value - prev:+.4f}"
        lines.append(f"| {metric} | {value:.4f} | {prev_str} | {change} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate performance report from load test outputs",
    )
    parser.add_argument("results", nargs="+", help="k6 summary JSON files")
    args = parser.parse_args()

    report_dir = Path("dashboards/performance/reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    metrics: Dict[str, float] = {}
    for result in args.results:
        path = Path(result)
        if not path.exists():
            continue
        parsed = parse_result(path)
        for name, value in parsed.items():
            metrics[f"{path.stem}_{name}"] = value

    previous = load_previous(report_dir)
    table = generate_table(metrics, previous)
    channels = alert_channels(Path("monitoring/alerts.yml"))
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    contents = [f"# Load Test Report - {timestamp}", "", table, ""]
    if channels:
        contents.append(f"Alert channels: {', '.join(channels)}")
    report_md = "\n".join(contents)

    # Store historical and latest reports
    (report_dir / f"report-{timestamp}.md").write_text(report_md)
    (report_dir / "latest.md").write_text(report_md)
    (report_dir / "latest.json").write_text(json.dumps(metrics, indent=2))

    print(report_md)


if __name__ == "__main__":
    main()
