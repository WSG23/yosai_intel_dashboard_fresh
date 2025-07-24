#!/usr/bin/env python3
"""Reorganize project files into the clean architecture layout."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

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


def migrate(mapping: dict[str, str], dry_run: bool) -> None:
    for src_rel, dest_rel in mapping.items():
        src = ROOT / src_rel
        dest = ROOT / dest_rel
        move_path(src, dest, dry_run)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate repository structure")
    parser.add_argument("--config", help="JSON file with directory mappings")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    args = parser.parse_args(argv)
    mapping = load_mapping(args.config)
    migrate(mapping, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual tool
    sys.exit(main())
