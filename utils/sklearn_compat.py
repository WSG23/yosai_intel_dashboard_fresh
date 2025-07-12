"""Optional scikit-learn imports with graceful fallbacks."""

from __future__ import annotations

import logging
from typing import Any, Type

logger = logging.getLogger(__name__)


def optional_import(name: str, fallback: Type | None = None) -> Any:
    """Attempt to import ``name`` returning ``fallback`` if unavailable."""
    try:
        module = __import__(name, fromlist=["*"])  # type: ignore
        return module
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning("Optional dependency '%s' unavailable: %s", name, exc)
        return fallback


__all__ = ["optional_import"]

