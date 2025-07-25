#!/usr/bin/env python3
"""Validate absence of legacy import paths."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from scripts.update_imports import PATTERNS, ROOT


def _check_file(path: Path, compiled: list[re.Pattern[str]]) -> list[str]:
    results = []
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        for pattern in compiled:
            if pattern.search(line):
                results.append(f"{path}:{lineno}:{line}")
                break
    return results


def verify_paths(paths: list[Path]) -> int:
    compiled = [re.compile(p) for p in PATTERNS]
    issues: list[str] = []
    for root in paths:
        for py_file in root.rglob("*.py"):
            issues.extend(_check_file(py_file, compiled))
    if issues:
        for issue in issues:
            print(issue)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check for legacy imports")
    parser.add_argument("paths", nargs="*", type=Path, default=[ROOT])
    args = parser.parse_args(argv)
    return verify_paths(args.paths)


if __name__ == "__main__":  # pragma: no cover - manual tool
    raise SystemExit(main())
