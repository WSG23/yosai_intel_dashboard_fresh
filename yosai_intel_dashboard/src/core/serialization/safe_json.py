from __future__ import annotations

"""Utility for recursively sanitizing objects for JSON serialization."""

import json
import logging
from dataclasses import asdict, is_dataclass
from typing import Any

from core.unicode import sanitize_unicode_input

try:  # Optional Flask-Babel
    from flask_babel import LazyString

    BABEL_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    LazyString = None  # type: ignore
    BABEL_AVAILABLE = False

try:
    from markupsafe import Markup

    MARKUP_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    Markup = None  # type: ignore
    MARKUP_AVAILABLE = False

logger = logging.getLogger(__name__)


class SafeJSONSerializer:
    """Recursively sanitize objects for safe JSON transport."""

    def serialize(self, obj: Any) -> Any:
        """Return a JSON-safe representation of ``obj``."""
        return self._sanitize(obj)

    def dumps(self, obj: Any, **kwargs: Any) -> str:
        """Serialize ``obj`` to JSON using :func:`json.dumps`."""
        sanitized = self.serialize(obj)
        return json.dumps(sanitized, ensure_ascii=False, **kwargs)

    # Internal helpers -----------------------------------------------------
    def _sanitize(self, obj: Any) -> Any:  # noqa: C901 - complexity ok
        try:
            if obj is None or isinstance(obj, (int, float, bool)):
                return obj

            if isinstance(obj, bytes):
                return sanitize_unicode_input(obj)

            if isinstance(obj, str):
                return sanitize_unicode_input(obj)

            if MARKUP_AVAILABLE and isinstance(obj, Markup):
                return sanitize_unicode_input(str(obj))

            if BABEL_AVAILABLE and LazyString and isinstance(obj, LazyString):
                return sanitize_unicode_input(str(obj))

            if isinstance(obj, dict):
                return {self._sanitize(k): self._sanitize(v) for k, v in obj.items()}

            if isinstance(obj, list):
                return [self._sanitize(v) for v in obj]

            if isinstance(obj, tuple):
                return tuple(self._sanitize(v) for v in obj)

            if is_dataclass(obj):
                return self._sanitize(asdict(obj))

            if hasattr(obj, "__dict__"):
                return {k: self._sanitize(v) for k, v in vars(obj).items()}
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning(f"SafeJSONSerializer failed: {exc}")
            return sanitize_unicode_input(str(obj))

        return obj
