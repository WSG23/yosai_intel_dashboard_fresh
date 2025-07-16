#!/usr/bin/env python3
"""Fail if pip-audit reports any critical vulnerabilities."""
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

    critical = []
    for entry in results:
        for vuln in entry.get("vulns", []):
            if vuln.get("severity", "").lower() == "critical":
                ident = vuln.get("id")
                pkg = entry.get("name")
                version = entry.get("version")
                critical.append(f"{pkg} {version}: {ident}")

    if critical:
        print("Critical vulnerabilities detected:")
        for item in critical:
            print(f"- {item}")
        return 1

    print("No critical vulnerabilities found.")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
