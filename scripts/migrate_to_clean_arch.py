#!/usr/bin/env python3
"""Reorganize project files into the clean architecture layout."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tarfile
from pathlib import Path

from migrate import _check_git_clean  # reuse helper from migrate.py

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAPPING = {
    "core": "yosai_intel_dashboard/src/core/domain",
    "models": "yosai_intel_dashboard/src/core/domain",
    "services": "yosai_intel_dashboard/src/services",
    "config": "yosai_intel_dashboard/src/infrastructure/config",
    "monitoring": "yosai_intel_dashboard/src/infrastructure/monitoring",
    "security": "yosai_intel_dashboard/src/infrastructure/security",
    "api": "yosai_intel_dashboard/src/adapters/api",
    "plugins": "yosai_intel_dashboard/src/adapters/api/plugins",
}


def gather_status(mapping: dict[str, str]) -> dict[str, str]:
    """Return migration status for each mapped directory."""
    status: dict[str, str] = {}
    for src_rel, dest_rel in mapping.items():
        src = ROOT / src_rel
        dest = ROOT / dest_rel
        if dest.exists() and not src.exists():
            status[src_rel] = "migrated"
        elif src.exists():
            status[src_rel] = "pending"
        else:
            status[src_rel] = "missing"
    return status


def print_report(status: dict[str, str]) -> None:
    pending = [src for src, st in status.items() if st == "pending"]
    migrated = sum(1 for st in status.values() if st == "migrated")
    found = sum(1 for st in status.values() if st != "missing")
    pct = (migrated / found * 100) if found else 0.0

    if pending:
        print("Directories pending migration:")
        for src in pending:
            print(f" - {src}")
    else:
        print("All mapped directories have been migrated.")
    print(f"Migrated {migrated}/{found} directories ({pct:.1f}%)")


def load_mapping(path: str | None) -> dict[str, str]:
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return DEFAULT_MAPPING


def move_path(src: Path, dest: Path, dry_run: bool) -> None:
    if not src.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"[DRY] {src} -> {dest}")
    else:
        print(f"Moving {src} -> {dest}")
        shutil.move(str(src), str(dest))


def create_backup(mapping: dict[str, str], archive: Path, dry_run: bool) -> None:
    """Archive the directories defined in ``mapping``."""
    if dry_run:
        print(f"[DRY] Creating backup {archive}")
        return
    with tarfile.open(archive, "w:gz") as tar:
        for src_rel in mapping.keys():
            src = ROOT / src_rel
            if src.exists():
                tar.add(src, arcname=src_rel)


def restore_backup(archive: Path, dry_run: bool) -> None:
    """Extract directories from ``archive`` into the repository root."""
    if dry_run:
        print(f"[DRY] Restoring from {archive}")
        return
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(path=ROOT)


def migrate(mapping: dict[str, str], dry_run: bool, backup_archive: Path | None = None) -> None:
    if backup_archive is not None:
        create_backup(mapping, backup_archive, dry_run)
    for src_rel, dest_rel in mapping.items():
        src = ROOT / src_rel
        dest = ROOT / dest_rel
        move_path(src, dest, dry_run)


def rollback(mapping: dict[str, str], archive: Path, dry_run: bool) -> None:
    for dest_rel in mapping.values():
        dest = ROOT / dest_rel
        if dest.exists():
            if dry_run:
                print(f"[DRY] Removing {dest}")
            else:
                shutil.rmtree(dest)
    restore_backup(archive, dry_run)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate repository structure")
    parser.add_argument("--config", help="JSON file with directory mappings")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument(
        "--backup",
        type=Path,
        help="Create backup archive before moving",
    )
    parser.add_argument(
        "--rollback",
        type=Path,
        help="Restore directories from the given backup archive",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Show migration status without moving files",
    )
    args = parser.parse_args(argv)

    mapping = load_mapping(args.config)
    if args.report:
        status = gather_status(mapping)
        print_report(status)
        return 0

    _check_git_clean()

    if args.rollback:
        rollback(mapping, args.rollback, args.dry_run)
    else:
        migrate(mapping, dry_run=args.dry_run, backup_archive=args.backup)

    status = gather_status(mapping)
    print_report(status)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual tool
    sys.exit(main())
