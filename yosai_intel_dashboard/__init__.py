"""Compatibility layer for the clean architecture transition."""
from __future__ import annotations

import importlib
import sys

_legacy_map = {
    "core": "core",
    "services": "services",
    "models": "models",
    "config": "config",
    "security": "security",
    "monitoring": "monitoring",
    "api": "api",
    "plugins": "plugins",
}

for old, new in _legacy_map.items():
    if old not in sys.modules:
        try:
            sys.modules[old] = importlib.import_module(new)
        except ModuleNotFoundError:
            continue
