"""Pytest configuration for the test-suite."""
from __future__ import annotations

import importlib.util
import warnings

pytest_plugins = ["tests.config"]

_missing_packages = [
    pkg for pkg in ("yaml", "psutil") if importlib.util.find_spec(pkg) is None
]
if _missing_packages:
    warnings.warn(
        "Missing required test dependencies: " + ", ".join(_missing_packages),
        RuntimeWarning,
    )
