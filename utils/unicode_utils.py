"""Legacy Unicode helpers.

This module now wraps :mod:`core.unicode` while preserving the old API.
Calling these functions will emit :class:`DeprecationWarning` directing you
 to the new implementations in :mod:`core.unicode`.
"""

from __future__ import annotations

import warnings
from typing import Any

import pandas as pd

from core import unicode as _u

# Public classes
UnicodeProcessor = _u.UnicodeProcessor
ChunkedUnicodeProcessor = _u.ChunkedUnicodeProcessor


def _warn(func_name: str) -> None:
    warnings.warn(
        f"{func_name} is deprecated; use core.unicode.{func_name}",
        DeprecationWarning,
        stacklevel=2,
    )


def clean_unicode_text(text: str) -> str:
    _warn("clean_unicode_text")
    return _u.clean_unicode_text(text)


def safe_decode_bytes(data: bytes, encoding: str = "utf-8") -> str:
    _warn("safe_decode_bytes")
    return _u.safe_decode_bytes(data, encoding)


def safe_encode_text(value: Any) -> str:
    _warn("safe_encode_text")
    return _u.safe_encode_text(value)


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    _warn("sanitize_dataframe")
    return _u.sanitize_dataframe(df)


def safe_unicode_encode(value: Any) -> str:
    _warn("safe_encode_text")
    return _u.safe_encode_text(value)


def safe_encode(value: Any) -> str:
    _warn("safe_encode_text")
    return _u.safe_encode_text(value)


def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
    _warn("safe_decode_bytes")
    return _u.safe_decode_bytes(data, encoding)


def handle_surrogate_characters(text: str) -> str:
    _warn("clean_unicode_text")
    return _u.handle_surrogate_characters(text)


def clean_unicode_surrogates(text: Any) -> str:
    _warn("clean_unicode_text")
    return _u.clean_unicode_surrogates(text)


def sanitize_unicode_input(text: Any) -> str:
    _warn("safe_encode_text")
    return _u.sanitize_unicode_input(text)


def sanitize_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    _warn("sanitize_dataframe")
    return _u.sanitize_dataframe(df)


__all__ = [
    "clean_unicode_text",
    "safe_decode_bytes",
    "safe_encode_text",
    "sanitize_dataframe",
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    "safe_unicode_encode",
    "safe_encode",
    "safe_decode",
    "handle_surrogate_characters",
    "clean_unicode_surrogates",
    "sanitize_unicode_input",
    "sanitize_data_frame",
]
