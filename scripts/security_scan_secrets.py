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


def entropy(value: str) -> float:
    if not value:
        return 0.0
    length = len(value)
    counts = Counter(value)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def main() -> None:
    secret = os.getenv("SECRET_KEY", "")
    errors = []
    if not secret or any(p.search(secret) for p in DEFAULT_PATTERNS) or entropy(secret) < 3.5:
        errors.append("Secret may be weak or missing")
    severity = "HIGH" if errors else "LOW"
    data = {
        "name": "Secrets scan",
        "severity": severity,
        "findings": errors,
        "remediation": "Rotate weak or missing secrets." if errors else "No action required",
    }
    with open("security_secrets_scan.json", "w", encoding="utf-8") as fh:
        json.dump(data, fh)


if __name__ == "__main__":
    main()
