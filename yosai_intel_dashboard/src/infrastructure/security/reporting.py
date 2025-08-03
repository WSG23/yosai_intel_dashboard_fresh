"""Aggregate security events and validation violations for reporting."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

from prometheus_client import REGISTRY, Gauge
from prometheus_client.core import CollectorRegistry

# Prometheus metrics - handle re-registration in tests
if "security_events_total" not in REGISTRY._names_to_collectors:
    EVENT_GAUGE = Gauge(
        "security_events_total",
        "Security events grouped by type and severity",
        ["type", "severity"],
    )
    VIOLATION_GAUGE = Gauge(
        "security_violations_total",
        "Security validator violations by issue",
        ["issue"],
    )
else:  # pragma: no cover - defensive
    EVENT_GAUGE = Gauge(
        "security_events_total",
        "Security events grouped by type and severity",
        ["type", "severity"],
        registry=CollectorRegistry(),
    )
    VIOLATION_GAUGE = Gauge(
        "security_violations_total",
        "Security validator violations by issue",
        ["issue"],
        registry=CollectorRegistry(),
    )

REMEDIATION_TIPS: Dict[str, str] = {
    "xss": "Escape user input and encode output to prevent cross-site scripting.",
    "sql_injection": "Use parameterized queries and avoid building SQL with string concatenation.",
    "insecure_deserialization": "Avoid deserializing untrusted data; prefer safe formats like JSON.",
    "ssrf": "Validate URLs and block internal addresses to prevent SSRF.",
}


def _get_auditor():
    from yosai_intel_dashboard.src.core.security import security_auditor

    return security_auditor


def _parse_since(value: str) -> int:
    """Return hours represented by ``value`` (e.g. ``'24h'``)."""
    if value.endswith("h"):
        return int(value[:-1])
    raise ValueError(f"Unsupported duration format: {value}")


def _collect_events(hours: int) -> Tuple[Dict[Tuple[str, str], int], Dict[str, int]]:
    """Return counts for events and validation issues within ``hours``."""
    cutoff = datetime.now() - timedelta(hours=hours)
    event_counts: Dict[Tuple[str, str], int] = {}
    violations: Dict[str, int] = {}

    auditor = _get_auditor()
    for event in auditor.events:
        if event.timestamp < cutoff:
            continue
        key = (event.event_type, event.severity.value)
        event_counts[key] = event_counts.get(key, 0) + 1
        if event.event_type == "input_validation_failed":
            for issue in event.details.get("issues", []):
                violations[issue] = violations.get(issue, 0) + 1

    return event_counts, violations


def update_metrics(
    event_counts: Dict[Tuple[str, str], int], violations: Dict[str, int]
) -> None:
    """Update Prometheus gauges from ``event_counts`` and ``violations``."""
    EVENT_GAUGE.clear()
    VIOLATION_GAUGE.clear()
    for (etype, severity), count in event_counts.items():
        EVENT_GAUGE.labels(type=etype, severity=severity).set(count)
    for issue, count in violations.items():
        VIOLATION_GAUGE.labels(issue=issue).set(count)


def generate_report(hours: int = 24) -> Dict[str, Any]:
    """Generate security report for the last ``hours`` hours."""
    auditor = _get_auditor()
    summary = auditor.get_security_summary(hours)
    event_counts, violations = _collect_events(hours)
    remediation = {
        issue: REMEDIATION_TIPS.get(issue, "Refer to security guidelines.")
        for issue in violations
    }
    summary["violations"] = violations
    update_metrics(event_counts, violations)
    return {
        "generated_at": datetime.now().isoformat(),
        "lookback_hours": hours,
        "summary": summary,
        "remediation": remediation,
    }


def report_to_json(report: Dict[str, Any]) -> str:
    """Return a pretty-printed JSON representation of ``report``."""
    return json.dumps(report, default=str, indent=2)


def report_to_html(report: Dict[str, Any]) -> str:
    """Return ``report`` rendered as simple HTML."""
    lines = [
        "<html>",
        "<body>",
        "<h1>Security Report</h1>",
        f"<p>Generated at: {report['generated_at']}</p>",
        f"<p>Lookback: {report['lookback_hours']}h</p>",
        "<h2>Violations</h2>",
        "<ul>",
    ]
    for issue, count in report["summary"].get("violations", {}).items():
        tip = report["remediation"].get(issue, "")
        lines.append(f"<li>{issue}: {count} - {tip}</li>")
    lines.extend(["</ul>", "</body>", "</html>"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate security report")
    parser.add_argument("--since", default="24h", help="Lookback window, e.g. 24h")
    args = parser.parse_args(argv)
    hours = _parse_since(args.since)
    report = generate_report(hours)
    print(report_to_json(report))
    print(report_to_html(report))


if __name__ == "__main__":  # pragma: no cover - CLI
    main()

