"""Pytest configuration for the test-suite."""
from __future__ import annotations

import importlib.util
import warnings

from . import optional_dependency_config  # registers stubs

_missing_packages = [
    pkg for pkg in ("yaml", "psutil") if importlib.util.find_spec(pkg) is None
]
if _missing_packages:
    warnings.warn(
        "Missing required test dependencies: " + ", ".join(_missing_packages),
        RuntimeWarning,
    )
