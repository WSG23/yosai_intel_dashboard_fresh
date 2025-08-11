"""Compatibility shim for the legacy ``core`` package.

This module re-exports the canonical ``yosai_intel_dashboard.src.core`` package
so that imports like ``import core.integrations`` continue to work.
"""

import sys

from yosai_intel_dashboard.src import core as _core
from yosai_intel_dashboard.src.core import integrations

# Expose submodules for import core.integrations
sys.modules[__name__ + ".integrations"] = integrations

__all__ = getattr(_core, "__all__", [])
for name in __all__:
    try:
        globals()[name] = getattr(_core, name)
    except AttributeError:
        pass
