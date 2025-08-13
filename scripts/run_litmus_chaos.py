#!/usr/bin/env python3
"""Apply Litmus Chaos experiments and wait for completion."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAOS_DIR = ROOT / "deploy" / "chaos"
if not CHAOS_DIR.exists():  # Backward compatibility with old location
    CHAOS_DIR = ROOT / "k8s" / "chaos"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def apply_manifests() -> None:
    for manifest in sorted(CHAOS_DIR.glob("*.yaml")):
        run(["kubectl", "apply", "-f", str(manifest)])


def main() -> None:
    apply_manifests()
    print("Chaos experiments applied")


if __name__ == "__main__":
    main()
