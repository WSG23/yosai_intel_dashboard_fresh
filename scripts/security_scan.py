#!/usr/bin/env python3
"""Placeholder script to scan for SQL, XSS, IDOR and file upload issues.

This script performs lightweight pattern checks to simulate a security scan. It
writes its results to ``security_code_scan.json`` for downstream reporting.
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import List

RE_PATTERNS = {
    "SQL Injection": re.compile(r"exec_sql|raw\("),
    "XSS": re.compile(r"<script>|javascript:"),
    "Insecure Direct Object Reference": re.compile(r"idor"),
    "Unsafe File Upload": re.compile(r"file_upload"),
}

ROOT = pathlib.Path(__file__).resolve().parent.parent


def scan_repository() -> List[str]:
    """Scan repository files for insecure patterns (very naive)."""
    findings: List[str] = []
    for path in ROOT.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for name, pattern in RE_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{name} pattern found in {path.relative_to(ROOT)}")
    return findings


def main() -> None:
    findings = scan_repository()
    severity = "LOW" if not findings else "HIGH"
    data = {
        "name": "Code vulnerability scan",
        "severity": severity,
        "findings": findings,
        "remediation": "Review findings and sanitize inputs." if findings else "No action required",
    }
    with open("security_code_scan.json", "w", encoding="utf-8") as fh:
        json.dump(data, fh)


if __name__ == "__main__":
    main()
