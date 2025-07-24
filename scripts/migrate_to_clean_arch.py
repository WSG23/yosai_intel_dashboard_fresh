#!/usr/bin/env python3
"""Reorganize project files into the clean architecture layout."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
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


def backup_directory(src: Path, backup_root: Path, dry_run: bool) -> None:
    """Copy ``src`` into ``backup_root`` preserving directory structure."""
    if not src.exists():
        return
    dest = backup_root / src.relative_to(ROOT)
    if dry_run:
        print(f"[DRY] Backup {src} -> {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def restore_directory(src: Path, backup_root: Path, dry_run: bool) -> None:
    """Restore ``src`` from ``backup_root`` if a backup exists."""
    backup = backup_root / src.relative_to(ROOT)
    if not backup.exists():
        return
    if dry_run:
        print(f"[DRY] Restore {src} <- {backup}")
        return
    if src.exists():
        shutil.rmtree(src)
    shutil.copytree(backup, src)


def migrate(mapping: dict[str, str], dry_run: bool, backup_root: Path | None = None) -> None:
    for src_rel, dest_rel in mapping.items():
        src = ROOT / src_rel
        dest = ROOT / dest_rel
        if backup_root is not None:
            backup_directory(src, backup_root, dry_run)
        move_path(src, dest, dry_run)


def rollback(mapping: dict[str, str], backup_root: Path, dry_run: bool) -> None:
    for src_rel, dest_rel in mapping.items():
        src = ROOT / src_rel
        dest = ROOT / dest_rel
        if dest.exists():
            if dry_run:
                print(f"[DRY] Removing {dest}")
            else:
                shutil.rmtree(dest)
        restore_directory(src, backup_root, dry_run)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate repository structure")
    parser.add_argument("--config", help="JSON file with directory mappings")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument(
        "--backup",
        type=Path,
        help="Directory to store backups before moving",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Restore directories from backup",
    )
    args = parser.parse_args(argv)

    mapping = load_mapping(args.config)
    _check_git_clean()

    if args.rollback:
        if args.backup is None:
            raise SystemExit("--rollback requires --backup")
        rollback(mapping, args.backup, args.dry_run)
    else:
        migrate(mapping, dry_run=args.dry_run, backup_root=args.backup)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual tool
    sys.exit(main())
