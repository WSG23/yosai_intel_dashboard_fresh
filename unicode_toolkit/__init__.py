"""Unified Unicode utilities package."""

from .core import UnicodeProcessor
from .helpers import (
    UnicodeQueryHandler,
    clean_unicode_surrogates,
    clean_unicode_text,
    decode_upload_content,
    safe_encode_text,
    sanitize_dataframe,
)
from .sql_safe import encode_query

__all__ = [
    "UnicodeProcessor",
    "UnicodeValidator",
    "UnicodeSanitizer",
    "UnicodeEncoder",
    "clean_unicode_surrogates",
    "clean_unicode_text",
    "safe_encode_text",
    "UnicodeQueryHandler",
    "decode_upload_content",
    "sanitize_dataframe",
    "encode_query",
]


def __getattr__(name: str):
    if name == "UnicodeValidator":
        from importlib import import_module

        return import_module(
            "security.unicode_security_validator"
        ).UnicodeSecurityValidator
    if name == "UnicodeSanitizer":
        from core import unicode as _u

        return _u.sanitize_unicode_input
    if name == "UnicodeEncoder":
        from core import unicode as _u

        return _u.UnicodeSQLProcessor
    raise AttributeError(name)
