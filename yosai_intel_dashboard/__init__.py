"""Compatibility layer for the clean architecture transition."""
from __future__ import annotations

import importlib
import sys

_legacy_map = {
    "core": "yosai_intel_dashboard.src.core",
    "services": "yosai_intel_dashboard.src.services",
    "models": "yosai_intel_dashboard.src.core.domain",
}

for old, new in _legacy_map.items():
    if old not in sys.modules:
        try:
            sys.modules[old] = importlib.import_module(new)
        except ModuleNotFoundError:
            continue
