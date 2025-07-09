"""Simplified Unicode helpers used across the code base."""

from __future__ import annotations

import logging
import unicodedata
from typing import Any

from .unicode_processor import sanitize_unicode_input as _sanitize_unicode_input

logger = logging.getLogger(__name__)


class UnicodeNormalizationError(Exception):
    """Raised when Unicode normalization fails."""


def normalize_unicode_safely(text: Any, form: str = "NFKC") -> str:
    """Return ``text`` normalised using ``form`` with robust error handling."""

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to convert %r to str: %s", text, exc)
            raise UnicodeNormalizationError(str(exc)) from exc

    try:
        return unicodedata.normalize(form, text)
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Unicode normalization failed: %s", exc)
        raise UnicodeNormalizationError(str(exc)) from exc


def detect_surrogate_pairs(text: Any) -> bool:
    """Return ``True`` if ``text`` contains any UTF-16 surrogate pair."""

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:  # pragma: no cover - defensive
            return False

    for idx in range(len(text) - 1):
        first = ord(text[idx])
        second = ord(text[idx + 1])
        if 0xD800 <= first <= 0xDBFF and 0xDC00 <= second <= 0xDFFF:
            return True
    return False


def sanitize_for_utf8(value: Any) -> str:
    """Return ``value`` cleaned of surrogates and normalised for UTF-8."""

    cleaned = _sanitize_unicode_input(value)
    try:
        return normalize_unicode_safely(cleaned)
    except UnicodeNormalizationError as exc:  # pragma: no cover - best effort
        logger.warning("Returning unnormalised text due to error: %s", exc)
        return cleaned


__all__ = [
    "normalize_unicode_safely",
    "detect_surrogate_pairs",
    "sanitize_for_utf8",
    "UnicodeNormalizationError",
]


