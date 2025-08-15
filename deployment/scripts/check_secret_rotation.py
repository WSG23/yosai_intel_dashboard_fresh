#!/usr/bin/env python3
"""Check secrets for rotation requirements."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from yosai_intel_dashboard.src.core.secret_manager import SecretsManager

# Mapping of secret names to their required rotation frequency (in days)
ROTATION_POLICY = {
    "SECRET_KEY": 90,
    "DB_PASSWORD": 30,
}


def _last_rotated(name: str) -> datetime | None:
    ts = os.getenv(f"{name}_LAST_ROTATED")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def main() -> int:
    stale: list[str] = []
    for name, days in ROTATION_POLICY.items():
        last_rotated = _last_rotated(name)
        if last_rotated is None or SecretsManager.needs_rotation(last_rotated, days):
            stale.append(name)
    if stale:
        print("Secrets requiring rotation: " + ", ".join(stale))
        return 1
    print("All secrets satisfy rotation policy.")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
