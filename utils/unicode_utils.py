from __future__ import annotations

"""Common Unicode helper functions."""

import logging
import re
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)


def handle_surrogate_characters(text: str) -> str:
    """Return ``text`` with problematic surrogate characters sanitized."""
    try:
        cleaned = re.sub(r"[\uD800-\uDFFF]", "\uFFFD", text)
        cleaned = unicodedata.normalize("NFKC", cleaned)
        return cleaned.encode("utf-8", "replace").decode("utf-8")
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Surrogate character handling failed: %s", exc)
        return text.encode("utf-8", "replace").decode("utf-8")


def safe_unicode_encode(value: Any) -> str:
    """Convert ``value`` to a UTF-8 string, removing invalid surrogates."""
    try:
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8", "surrogatepass")
            except Exception:
                value = value.decode("latin-1", "surrogatepass")
        else:
            value = str(value)
        value = re.sub(r"[\ud800-\udfff]", "", value)
        return value.encode("utf-8", "ignore").decode("utf-8", "ignore")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Unicode encoding failed: %s", exc)
        return handle_surrogate_characters(str(value))


__all__ = ["safe_unicode_encode", "handle_surrogate_characters"]
