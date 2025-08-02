from __future__ import annotations

"""Create legacy symlinks for backward compatibility."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "yosai_intel_dashboard" / "src"

SYMLINKS = {
    "core": SRC_ROOT / "core",
    "models": SRC_ROOT / "models",
    "services": SRC_ROOT / "services",
    "config": SRC_ROOT / "infrastructure" / "config",
    "monitoring": SRC_ROOT / "infrastructure" / "monitoring",
    "security": SRC_ROOT / "infrastructure" / "security",
    "api": SRC_ROOT / "adapters" / "api",
    "plugins": SRC_ROOT / "adapters" / "api" / "plugins",
    "mapping": SRC_ROOT / "mapping",
    "database": SRC_ROOT / "database",
}

for name, target in SYMLINKS.items():
    link = ROOT / name
    if link.exists():
        continue
    if not target.exists():
        continue
    link.symlink_to(target)
    print(f"Created symlink {link} -> {target}")
