#!/usr/bin/env python3
"""Apply isort and custom import organization."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.organize_imports import ImportOrganizer


def main() -> int:
    subprocess.run(["isort", "."], check=True)
    organizer = ImportOrganizer()
    for path in Path(".").rglob("*.py"):
        organizer.organize_file(path)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
