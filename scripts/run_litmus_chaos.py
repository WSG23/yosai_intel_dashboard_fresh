#!/usr/bin/env python3
"""Apply Litmus Chaos experiments and wait for completion."""
from __future__ import annotations

import subprocess
from pathlib import Path

CHAOS_DIR = Path(__file__).resolve().parent.parent / "k8s" / "chaos"


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
