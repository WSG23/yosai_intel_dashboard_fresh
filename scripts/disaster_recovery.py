#!/usr/bin/env python3
"""Utility for automated backups and restoration."""

from __future__ import annotations

import argparse
import sys
import tarfile
from datetime import datetime
from pathlib import Path

BACKUP_ROOT = Path("backups")
TARGETS = [Path("database"), Path("config")]


def create_backup() -> Path:
    """Create a compressed backup archive of important directories."""
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    archive_path = BACKUP_ROOT / f"backup_{ts}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        for target in TARGETS:
            if target.exists():
                tar.add(target, arcname=target.name)
    return archive_path


def restore_backup(archive: Path) -> None:
    """Restore data from the provided backup archive."""
    if not archive.exists():
        raise FileNotFoundError(str(archive))
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(path=Path.cwd())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Disaster recovery utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("backup", help="Create a backup archive")
    restore_p = sub.add_parser("restore", help="Restore from a backup")
    restore_p.add_argument("archive", type=Path, help="Backup archive to restore")

    args = parser.parse_args(argv)
    if args.cmd == "backup":
        archive = create_backup()
        print(f"Backup created: {archive}")
        return 0
    if args.cmd == "restore":
        try:
            restore_backup(args.archive)
            print("Restoration complete")
            return 0
        except FileNotFoundError:
            print("Backup file not found", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
