#!/usr/bin/env python3
"""Generate API documentation for the project.

This script collects OpenAPI specifications from the various services and
writes them to a versioned directory under ``docs/api/<version>``.
The version is detected from ``pyproject.toml`` or the Go ``versioning``
module as a fallback.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

try:  # Python 3.11+
    import tomllib  # type: ignore
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore


ROOT = Path(__file__).resolve().parents[1]


def get_project_version() -> str:
    """Return project version from ``pyproject.toml`` or ``versioning`` module."""
    pyproject = ROOT / "pyproject.toml"
    if tomllib and pyproject.exists():
        data = tomllib.loads(pyproject.read_text())
        version = (
            data.get("project", {}).get("version")
            or data.get("tool", {}).get("poetry", {}).get("version")
        )
        if version:
            return str(version)

    version_file = ROOT / "versioning" / "versioning.go"
    if version_file.exists():
        match = re.search(r"currentVersion:\s*\"([^\"]+)\"", version_file.read_text())
        if match:
            return match.group(1)

    raise RuntimeError("Unable to determine project version")


def main() -> None:
    version = get_project_version()
    out_dir = ROOT / "docs" / "api" / version
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate specs using existing scripts
    subprocess.run(["go", "run", "./api/openapi"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/generate_fastapi_openapi.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/generate_flask_openapi.py"], cwd=ROOT, check=True)

    # Move generated files into the versioned directory
    for name in [
        "openapi.json",
        "analytics_microservice_openapi.json",
        "event_ingestion_openapi.json",
        "flask_openapi.json",
    ]:
        src = ROOT / "docs" / name
        if src.exists():
            shutil.move(str(src), out_dir / name)

    print(f"API docs written to {out_dir}")



if __name__ == "__main__":
    main()
