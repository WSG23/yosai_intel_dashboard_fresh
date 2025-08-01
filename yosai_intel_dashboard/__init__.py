"""Backward compatibility shims for the :mod:`yosai_intel_dashboard` package."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

# Attempt to import ``src`` eagerly for old import paths. This may fail when
# running in minimal environments, so guard the import to avoid raising an
# ``ImportError`` during module initialization.
try:
    _src = importlib.import_module(__name__ + ".src")
    sys.modules.setdefault(__name__ + ".src", _src)
except Exception:  # pragma: no cover - src may not be available
    _src = None

# Insert a lightweight proxy for ``yosai_intel_dashboard.models`` so that
# submodules can be imported without pulling in heavy dependencies up front.
_models_proxy = types.ModuleType(__name__ + ".models")
_models_proxy.__file__ = str(Path(__file__).resolve().parent / "src" / "models" / "__init__.py")
_models_proxy.__path__ = [str(Path(__file__).resolve().parent / "src" / "models")]
sys.modules.setdefault(__name__ + ".models", _models_proxy)


def __getattr__(name: str):
    """Lazily resolve optional submodules."""

    if name == "models":
        module = importlib.import_module(__name__ + ".models")
        sys.modules.setdefault(__name__ + ".models", module)
        globals()[name] = module
        return module

    if name == "src" and __name__ + ".src" in sys.modules:
        return sys.modules[__name__ + ".src"]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return module attributes for ``dir()``."""

    attrs = ["src", "models"]
    return sorted(attrs)
