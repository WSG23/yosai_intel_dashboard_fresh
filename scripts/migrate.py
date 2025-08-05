#!/usr/bin/env python3
"""Apply Alembic migrations with safety checks and rollback support."""
# flake8: noqa: E402
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yosai_intel_dashboard.src.database.migrations import MigrationManager

LOG = logging.getLogger(__name__)


def _check_git_clean() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True
    )
    if result.stdout.strip():
        raise SystemExit("Refusing to run with uncommitted changes")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("revision", nargs="?", default="head")
    parser.add_argument("--config", default="migrations/alembic.ini")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Emit SQL without executing",
    )
    args = parser.parse_args(argv)

    _check_git_clean()
    config_path = Path(args.config)
    if not config_path.is_file():
        raise SystemExit(f"Config file not found: {config_path}")
    mgr = MigrationManager(str(config_path))
    try:
        mgr.upgrade(args.revision, dry_run=args.dry_run)
    except Exception as exc:
        LOG.error("Migration failed: %s", exc)
        mgr.rollback()
        return 1
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(main())
