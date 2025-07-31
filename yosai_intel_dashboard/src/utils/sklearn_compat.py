"""Optional scikit-learn imports with graceful fallbacks."""

from __future__ import annotations

import logging
from typing import Any, Type

logger = logging.getLogger(__name__)


def optional_import(name: str, fallback: Type | None = None) -> Any:
    """Attempt to import ``name`` returning ``fallback`` if unavailable."""
    try:
        # Handle specific sklearn submodule imports
        if name.startswith("sklearn."):
            parts = name.split(".")
            if len(parts) > 2:  # e.g., sklearn.ensemble.IsolationForest
                module_path = ".".join(parts[:-1])  # sklearn.ensemble
                class_name = parts[-1]  # IsolationForest
                module = __import__(module_path, fromlist=[class_name])
                return getattr(module, class_name)
            else:
                module = __import__(name, fromlist=["*"])
        else:
            module = __import__(name, fromlist=["*"])
        return module
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning(f"Optional dependency '{name}' unavailable: {exc}")
        return fallback


__all__ = ["optional_import"]
