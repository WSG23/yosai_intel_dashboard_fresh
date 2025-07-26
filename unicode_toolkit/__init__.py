"""Compatibility wrappers providing legacy entry points."""

from __future__ import annotations

from core.unicode import (
    UnicodeSQLProcessor,
    sanitize_dataframe,
    safe_encode_text,
    clean_unicode_surrogates,
    clean_unicode_text,
    sanitize_unicode_input,
    UnicodeProcessor,
)
from security.unicode_security_validator import UnicodeSecurityValidator as UnicodeValidator

from .helpers import decode_upload_content, UnicodeQueryHandler

__all__ = [
    "UnicodeProcessor",
    "UnicodeValidator",
    "UnicodeSQLProcessor",
    "UnicodeQueryHandler",
    "decode_upload_content",
    "clean_unicode_text",
    "clean_unicode_surrogates",
    "safe_encode_text",
    "sanitize_dataframe",
    "sanitize_unicode_input",
]
