"""Backward compatibility shims for the :mod:`yosai_intel_dashboard` package."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

# Import ``src`` eagerly using :func:`importlib.import_module` to avoid circular
# dependencies while keeping compatibility with old import paths.
_src = importlib.import_module(".src", __name__)
sys.modules.setdefault(__name__ + ".src", _src)

# Insert a lightweight proxy for ``yosai_intel_dashboard.models`` so that
# submodules can be imported without pulling in heavy dependencies up front.
_models_proxy = types.ModuleType(__name__ + ".models")
_models_proxy.__file__ = str(Path(__file__).resolve().parent / "src" / "models" / "__init__.py")
_models_proxy.__path__ = [str(Path(__file__).resolve().parent / "src" / "models")]


def _load_models():
    module = importlib.import_module(".models", __name__)
    sys.modules[__name__ + ".models"] = module
    globals()["models"] = module
    return module


def _models_getattr(attr: str):
    module = _load_models()
    return getattr(module, attr)


_models_proxy.__getattr__ = _models_getattr  # type: ignore[attr-defined]
sys.modules.setdefault(__name__ + ".models", _models_proxy)


def __getattr__(name: str):
    """Lazily import :mod:`models` on first access."""

    if name == "models":
        return _load_models()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
