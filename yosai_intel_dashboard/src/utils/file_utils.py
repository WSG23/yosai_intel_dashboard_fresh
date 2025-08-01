from __future__ import annotations

"""Helper utilities for working with files."""

from yosai_intel_dashboard.src.core.unicode import safe_unicode_decode
from security.unicode_security_validator import UnicodeSecurityValidator

_validator = UnicodeSecurityValidator()


def safe_decode_with_unicode_handling(data: bytes, encoding: str) -> str:
    """Decode bytes using ``encoding`` and sanitize output."""
    text = safe_unicode_decode(data, encoding)
    cleaned = _validator.validate_and_sanitize(text)
    return cleaned.replace("\ufffd", "")


__all__ = ["safe_decode_with_unicode_handling"]
