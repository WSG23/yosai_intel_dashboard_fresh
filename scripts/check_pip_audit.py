#!/usr/bin/env python3
"""Fail if pip-audit reports any critical vulnerabilities."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main(path: str = "audit-report.json") -> int:
    try:
        data = Path(path).read_text()
    except FileNotFoundError:
        print(f"Report file {path} not found", file=sys.stderr)
        return 1

    try:
        results = json.loads(data)
    except json.JSONDecodeError as exc:
        print("Failed to parse pip-audit JSON", file=sys.stderr)
        print(data)
        return 1

    critical_items = (
        f"{entry.get('name')} {entry.get('version')}: {vuln.get('id')}"
        for entry in results
        for vuln in entry.get("vulns", [])
        if vuln.get("severity", "").lower() == "critical"
    )
    first = next(critical_items, None)
    if first:
        print("Critical vulnerabilities detected:")
        print(f"- {first}")
        for item in critical_items:
            print(f"- {item}")
        return 1

    print("No critical vulnerabilities found.")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
