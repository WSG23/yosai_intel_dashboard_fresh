#!/usr/bin/env python3
"""Generate documentation about deprecated components."""
from __future__ import annotations

from pathlib import Path

import yaml

YAML_FILE = Path("deprecation.yml")
OUTPUT_FILE = Path("docs/deprecation_timeline.md")


def generate_docs(yaml_path: Path = YAML_FILE, output_path: Path = OUTPUT_FILE) -> None:
    """Read deprecation data and write the markdown summary."""
    if not yaml_path.exists():
        raise FileNotFoundError(f"{yaml_path} not found")

    entries = yaml.safe_load(yaml_path.read_text()) or []

    lines = [
        "# Deprecation Timeline",
        "",
        "This file is auto-generated from `deprecation.yml`.",
        "",
        "| Component | Deprecated Since | Removal Version |",
        "|-----------|-----------------|-----------------|",
    ]

    for item in entries:
        comp = item.get("component", "-")
        since = item.get("deprecated_since", "-")
        removal = item.get("removal_version", "-")
        lines.append(f"| {comp} | {since} | {removal} |")

    lines.extend(
        [
            "",
            "## Migration Guides",
            "",
            "Migration instructions for deprecated components will appear here.",
            "",
            "## Impact Analysis",
            "",
            "This section will detail user impact and remediation steps.",
            "",
            "## Monitoring",
            "",
            "Deprecated component usage is tracked via the `deprecation_usage_total` Prometheus metric.",
            "The Grafana dashboard lives in `dashboards/grafana/deprecation-usage.json` and alert rules",
            "are defined in `monitoring/prometheus/rules/deprecation_alerts.yml`.",
            "",
        ]
    )

    output_path.write_text("\n".join(lines))


if __name__ == "__main__":
    generate_docs()
