#!/usr/bin/env python3
"""Scan application secrets for common weaknesses."""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter

DEFAULT_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in ["dev", "development", "test", "secret", "change[-_]?me"]
]
CREDENTIAL_NAME_PATTERN = re.compile(
    r"(PASSWORD|SECRET|TOKEN|KEY|CREDENTIAL)", re.IGNORECASE
)


def entropy(value: str) -> float:
    if not value:
        return 0.0
    length = len(value)
    counts = Counter(value)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def main() -> None:
    target_vars = {"SECRET_KEY", "DB_PASSWORD", "AUTH0_CLIENT_SECRET"}
    for name in os.environ:
        if CREDENTIAL_NAME_PATTERN.search(name):
            target_vars.add(name)

    results = []
    for name in sorted(target_vars):
        value = os.getenv(name, "")
        issues: list[str] = []
        if not value:
            issues.append("Value is missing")
        else:
            if any(p.search(value) for p in DEFAULT_PATTERNS):
                issues.append("Contains common weak pattern")
            if entropy(value) < 3.5:
                issues.append("Low entropy")
        severity = "HIGH" if issues else "LOW"
        results.append({"variable": name, "severity": severity, "issues": issues})

    overall_severity = "HIGH" if any(r["severity"] == "HIGH" for r in results) else "LOW"
    data = {
        "name": "Secrets scan",
        "overall_severity": overall_severity,
        "results": results,
        "remediation": (
            "Rotate weak or missing secrets." if overall_severity == "HIGH" else "No action required"
        ),
    }
    with open("security_secrets_scan.json", "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    if overall_severity == "HIGH":
        raise SystemExit("High severity secrets detected")


if __name__ == "__main__":
    main()

