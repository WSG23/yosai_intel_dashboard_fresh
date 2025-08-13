#!/usr/bin/env python3
"""Check that Avro schema changes include a version bump.

The script inspects files under ``schemas/avro`` that changed compared to the
main branch. Any modified or deleted schema files will cause a failure because
new versions must be added as separate files.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SCHEMA_DIR = Path("schemas/avro")
VERSION_RE = re.compile(r"_v(\d+)\.avsc$")


def _git_diff() -> list[tuple[str, str]]:
    """Return (status, path) tuples for schema files changed from main."""
    try:
        base = (
            subprocess.check_output(
                ["git", "merge-base", "HEAD", "origin/main"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            or "HEAD~1"
        )
    except Exception:
        base = "HEAD~1"
    out = subprocess.check_output(
        ["git", "diff", "--name-status", base, "--", str(SCHEMA_DIR)],
        text=True,
        stderr=subprocess.DEVNULL,
    )
    results: list[tuple[str, str]] = []
    for line in out.splitlines():
        if not line:
            continue
        status, path = line.split("\t", 1)
        results.append((status, path))
    return results


def main() -> int:
    issues: list[str] = []
    for status, path in _git_diff():
        rel = Path(path)
        match = VERSION_RE.search(rel.name)
        if status != "A":
            issues.append(
                f"{rel} was {status} - schemas must be added with a new version file"
            )
            continue
        if not match:
            issues.append(f"{rel} does not include version suffix _vN.avsc")
            continue
        base_name = rel.name[: match.start()]
        existing = sorted(SCHEMA_DIR.glob(f"{base_name}*_v*.avsc"))
        if len(existing) > 1:
            latest = max(
                int(VERSION_RE.search(p.name).group(1))  # type: ignore[union-attr]
                for p in existing
                if p.name != rel.name
            )
            new_version = int(match.group(1))
            if new_version <= latest:
                issues.append(
                    f"{rel} version {new_version} not greater than existing {latest}"
                )
    if issues:
        print("Schema version check failed:")
        for msg in issues:
            print(" -", msg)
        return 1
    print("Schema version check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
