"""Compatibility shim for the legacy ``core`` package.

This module re-exports the canonical ``yosai_intel_dashboard.src.core`` package
without statically importing it during type checking. The upstream package has
many optional dependencies which are expensive for ``mypy`` to analyze. By
loading it dynamically we keep the runtime behaviour while avoiding unwanted
imports when running the stricter ``mypy`` checks.
"""

from importlib import import_module
import sys
from types import ModuleType
from typing import List, cast

# Load the real core package dynamically so mypy treats it as an opaque module.
_core: ModuleType = import_module("yosai_intel_dashboard.src.core")
integrations: ModuleType = import_module("yosai_intel_dashboard.src.core.integrations")

# Expose submodules for ``import core.integrations``
sys.modules[__name__ + ".integrations"] = integrations

# Re-export the public attributes of the real core package
__all__: List[str] = cast(List[str], getattr(_core, "__all__", []))
for name in __all__:
    try:
        globals()[name] = getattr(_core, name)
    except AttributeError:
        pass
