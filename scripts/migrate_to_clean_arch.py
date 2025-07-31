#!/usr/bin/env python3
"""Migrate legacy packages to the clean architecture layout."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "yosai_intel_dashboard" / "src"

# Mapping of legacy directory -> destination relative to SRC_ROOT
MOVE_MAP = {
    "core": "core",
    "models": "models",
    "services": "services",
    "config": "infrastructure/config",
    "monitoring": "infrastructure/monitoring",
    "security": "infrastructure/security",
    "api": "adapters/api",
    "plugins": "adapters/api/plugins",
}


def create_wrapper(name: str, target: str) -> None:
    """Create a thin module that re-exports the target package."""
    path = ROOT / f"{name}.py"
    module = f"yosai_intel_dashboard.src.{target.replace(os.sep, '.')}"
    path.write_text(
        "from importlib import import_module as _im\n"
        "import sys as _sys\n"
        f"_sys.modules[__name__] = _im('{module}')\n"
    )


def backup_dirs(archive: Path) -> None:
    """Archive all directories that will be moved."""
    with tarfile.open(archive, "w:gz") as tar:
        for name in MOVE_MAP:
            path = ROOT / name
            if path.exists():
                tar.add(path, arcname=name)


def restore_dirs(archive: Path) -> None:
    """Restore directories from the provided archive."""
    for name, dest in MOVE_MAP.items():
        (ROOT / f"{name}.py").unlink(missing_ok=True)
        dest_path = SRC_ROOT / dest
        if dest_path.exists():
            shutil.rmtree(dest_path)
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(path=ROOT)


def move_dirs(dry_run: bool) -> list[str]:
    """Move legacy directories into the new layout."""
    moved: list[str] = []
    for name, dest in MOVE_MAP.items():
        src = ROOT / name
        dst = SRC_ROOT / dest
        if not src.exists() or dst.exists():
            continue
        if dry_run:
            print(f"Would move {src} -> {dst}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), dst)
        create_wrapper(name, dest)
        moved.append(name)
    return moved


def report_status() -> str:
    migrated = 0
    total = len(MOVE_MAP)
    lines = []
    for name, dest in MOVE_MAP.items():
        dst = SRC_ROOT / dest
        status = "Migrated" if dst.exists() else "Pending"
        if status == "Migrated":
            migrated += 1
        lines.append(f"{name:<10} -> {dest:<25} {status}")
    percent = int(migrated / total * 100)
    lines.append(f"Migrated {migrated} of {total} directories ({percent}%)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Move packages to clean architecture layout"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview actions without changing files"
    )
    parser.add_argument(
        "--backup", type=Path, help="Create a backup archive before migrating"
    )
    parser.add_argument("--rollback", type=Path, help="Restore from a backup archive")
    parser.add_argument(
        "--report", action="store_true", help="Show migration progress and exit"
    )
    args = parser.parse_args(argv)

    if args.report and not any([args.backup, args.rollback, args.dry_run]):
        print(report_status())
        return 0

    if args.rollback is not None:
        restore_dirs(args.rollback)
        print("Rollback complete")
        print(report_status())
        return 0

    if args.backup is not None:
        backup_dirs(args.backup)
        print(f"Backup created at {args.backup}")

    moved = move_dirs(args.dry_run)

    if moved and not args.dry_run:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "update_imports.py")])

    print(report_status())
    return 0


if __name__ == "__main__":  # pragma: no cover - manual tool
    raise SystemExit(main())
