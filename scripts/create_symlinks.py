#!/usr/bin/env python3
"""Create legacy symlinks for the new clean architecture layout."""
from pathlib import Path


def ensure_symlink(src: Path, dest: Path) -> None:
    """Ensure *dest* is a symlink pointing to *src*."""
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.symlink_to(src)


def main() -> None:
    root = Path("/app/yosai_intel_dashboard")
    src_services = root / "src" / "services"
    legacy_services = root / "services"
    if src_services.exists():
        ensure_symlink(src_services, legacy_services)


if __name__ == "__main__":
    main()

