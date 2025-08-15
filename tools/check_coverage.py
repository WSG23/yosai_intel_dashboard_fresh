#!/usr/bin/env python3
"""Fail if any non-test Python module lacks coverage."""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

THRESHOLD = 1.0  # minimum percent coverage required


def main(report: str = "coverage.xml") -> int:
    path = Path(report)
    if not path.exists():
        print(f"coverage report not found: {report}")
        return 1
    tree = ET.parse(path)
    root = tree.getroot()
    failures: list[tuple[str, float]] = []
    for cls in root.findall(".//class"):
        filename = cls.attrib.get("filename", "")
        if filename.startswith("tests/") or filename.endswith("__init__.py"):
            continue
        rate = float(cls.attrib.get("line-rate", "0")) * 100
        if rate < THRESHOLD:
            failures.append((filename, rate))
    if failures:
        for name, rate in failures:
            print(f"{name} has insufficient coverage: {rate:.1f}%")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
