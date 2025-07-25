
"""Compatibility package for new clean architecture layout.

This module exposes the existing ``core`` package under the
``yosai_intel_dashboard.src`` namespace so that imports using the new
path continue to work until the package is fully migrated.
"""

from __future__ import annotations

from pathlib import Path

# Include the legacy ``core`` package in the module search path.  This
# mirrors the behaviour of a namespace package and allows statements like
# ``import yosai_intel_dashboard.src.core.service_container`` to resolve
# to the modules in the top-level ``core`` package.
__path__.append(str(Path(__file__).resolve().parents[3] / "core"))
