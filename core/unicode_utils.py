"""Simplified Unicode helpers used across the code base."""

from __future__ import annotations

import logging
import unicodedata
from typing import Any

from security.unicode_security_validator import (
    UnicodeSecurityValidator,
    SecurityError,
)

_validator = UnicodeSecurityValidator()

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

    return _validator._contains_surrogates(str(text))


def sanitize_for_utf8(value: Any) -> str:
    """Return ``value`` cleaned and safe for UTF-8."""

    try:
        return _validator.validate_and_sanitize(value)
    except SecurityError:
        raise
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Unicode sanitization failed: %s", exc)
        return _validator.validate_and_sanitize(str(value))


__all__ = [
    "normalize_unicode_safely",
    "detect_surrogate_pairs",
    "sanitize_for_utf8",
    "UnicodeNormalizationError",
]
