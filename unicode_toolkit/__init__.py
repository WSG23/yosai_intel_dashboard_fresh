"""Compatibility wrappers providing legacy entry points."""

from __future__ import annotations

from yosai_intel_dashboard.src.core.unicode import (
    UnicodeProcessor,
    UnicodeSQLProcessor,
    clean_unicode_surrogates,
    clean_unicode_text,
    safe_encode_text,
    sanitize_dataframe,
    sanitize_unicode_input,
)
from security.unicode_security_validator import (
    UnicodeSecurityValidator as UnicodeValidator,
)

from .helpers import UnicodeQueryHandler, decode_upload_content

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
