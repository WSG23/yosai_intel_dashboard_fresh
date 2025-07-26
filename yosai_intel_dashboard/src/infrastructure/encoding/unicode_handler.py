from __future__ import annotations

"""High level Unicode handling utilities."""

from typing import Any, List, Tuple
import unicodedata

from core.unicode import clean_surrogate_chars
from security.unicode_security_validator import UnicodeSecurityValidator


_ZERO_WIDTH = [
    "\u200b",
    "\u200c",
    "\u200d",
    "\u2060",
]


class UnicodeHandler:
    """Utility class for sanitizing and validating Unicode text."""

    _validator = UnicodeSecurityValidator()

    @staticmethod
    def _remove_zero_width(text: str) -> str:
        for ch in _ZERO_WIDTH:
            text = text.replace(ch, "")
        return text

    @classmethod
    def sanitize(cls, text: Any) -> str:
        cleaned = clean_surrogate_chars(str(text))
        cleaned = cleaned.replace("\ufeff", "")
        cleaned = cls._remove_zero_width(cleaned)
        cleaned = cls._validator.validate_and_sanitize(cleaned)
        try:
            cleaned = unicodedata.normalize("NFC", cleaned)
        except Exception:
            pass
        return cleaned

    @staticmethod
    def validate_utf8(data: bytes) -> bool:
        try:
            data.decode("utf-8")
            return True
        except Exception:
            return False

    @classmethod
    def repair_text(cls, text: Any) -> Tuple[str, List[str]]:
        issues: List[str] = []
        original = str(text)
        cleaned = clean_surrogate_chars(original)
        if cleaned != original:
            issues.append("surrogates_removed")
        if "\ufeff" in cleaned:
            issues.append("bom_removed")
            cleaned = cleaned.replace("\ufeff", "")
        pre_zero = cleaned
        cleaned = cls._remove_zero_width(cleaned)
        if cleaned != pre_zero:
            issues.append("zero_width_removed")
        cleaned = cls._validator.validate_and_sanitize(cleaned)
        try:
            normalized = unicodedata.normalize("NFC", cleaned)
            if normalized != cleaned:
                issues.append("normalized")
            cleaned = normalized
        except Exception:
            issues.append("normalization_failed")
        return cleaned, issues


__all__ = ["UnicodeHandler"]
