#!/usr/bin/env python3
"""Scan the repository for secrets using detect-secrets.

This wrapper ensures a shared workflow for secret scanning. It will
compare the current state of the repository against the stored baseline
and exit with a non-zero status if new secrets are detected.

If the baseline does not exist yet, it will be generated automatically.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = REPO_ROOT / ".secrets.baseline"
REPORT_PATH = REPO_ROOT / "secret-scan-report.json"


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def generate_baseline() -> None:
    result = _run(["detect-secrets", "scan", str(REPO_ROOT)])
    BASELINE_PATH.write_text(result.stdout)
    print(f"Baseline created at {BASELINE_PATH}")


def main() -> int:
    if not BASELINE_PATH.exists():
        generate_baseline()
        return 0

    result = _run(
        [
            "detect-secrets",
            "scan",
            "--baseline",
            str(BASELINE_PATH),
            str(REPO_ROOT),
        ]
    )

    REPORT_PATH.write_text(result.stdout or "{}")

    if result.returncode != 0:
        print("Potential secrets detected. See secret-scan-report.json for details.")
        print(
            "Remove the secrets or run 'detect-secrets audit .secrets.baseline' "
            "to update the baseline if these are false positives."
        )
    else:
        print("No new secrets detected.")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
