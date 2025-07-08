#!/usr/bin/env python3
"""Scan test files for dynamic import patterns."""
from __future__ import annotations

from pathlib import Path

PATTERNS = {
    "sys.modules": "sys.modules",
    "spec_from_file_location": "spec_from_file_location",
    "sys.path.append": "sys.path.append",
}


def find_offenses() -> list[tuple[Path, int, str]]:
    offenses: list[tuple[Path, int, str]] = []
    for path in Path("tests").rglob("*.py"):
        with path.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                for key, pattern in PATTERNS.items():
                    if pattern in line:
                        offenses.append((path.resolve(), lineno, key))
    return offenses


def main() -> None:
    offenses = find_offenses()
    if offenses:
        print("Dynamic import patterns found:\n")
        for path, lineno, pattern in offenses:
            rel_path = path.relative_to(Path.cwd())
            print(f"{rel_path}:{lineno}: {pattern}")
    else:
        print("No offending patterns found.")


if __name__ == "__main__":
    main()
