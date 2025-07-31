#!/usr/bin/env python3
"""Ensure the repository follows the clean architecture layout."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DIRS = [
    "models",
    "yosai_intel_dashboard/src/core/use_cases",
    "yosai_intel_dashboard/src/core/interfaces",
    "api",
    "yosai_intel_dashboard/src/adapters/persistence",
    "yosai_intel_dashboard/src/adapters/ui",
    "config",
    "security",
    "monitoring",
    "yosai_intel_dashboard/src/services/analytics",
    "yosai_intel_dashboard/src/services/events",
    "yosai_intel_dashboard/src/services/ml",
]


def main() -> int:
    missing = []
    for rel in REQUIRED_DIRS:
        path = ROOT / rel
        if not path.is_dir():
            missing.append(rel)
    if missing:
        for m in missing:
            print(f"Missing required directory: {m}")
        return 1
    print("Clean architecture directory structure validated.")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual tool
    sys.exit(main())
