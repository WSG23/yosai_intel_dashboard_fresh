"""Enterprise-grade Unicode utilities and migration helpers.

This module consolidates fragmented Unicode handling logic into a single,
robust implementation.  All new code should use the preferred API functions
defined here.  Legacy helpers remain available for backwards compatibility and
emit :class:`DeprecationWarning` when called.
"""

from __future__ import annotations

import logging
import re
import unicodedata
import warnings
from typing import Any, Callable, Iterable, Optional

from .unicode_processor import contains_surrogates

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Precompiled regular expressions used throughout the module
_CONTROL_RE = re.compile(r"[\x00-\x1F\x7F]")
_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")
_DANGEROUS_PREFIX_RE = re.compile(r"^[=+\-@]+")


def _drop_dangerous_prefix(text: str) -> str:
    """Remove characters that can trigger spreadsheet formula injection."""

    return _DANGEROUS_PREFIX_RE.sub("", text)


# ---------------------------------------------------------------------------
# Core classes

class UnicodeProcessor:
    """Centralised Unicode processing utilities."""

    REPLACEMENT_CHAR: str = "\uFFFD"

    # ------------------------------------------------------------------
    # Basic cleaning helpers
    # ------------------------------------------------------------------
    @staticmethod
    def clean_text(text: Any, replacement: str = "") -> str:
        """Return ``text`` with unsafe characters removed.

        Parameters
        ----------
        text:
            Input text. Non-string values are coerced via ``str()``.
        replacement:
            Replacement text for surrogate characters.  The default is to
            remove them entirely.
        """

        if text is None or (isinstance(text, float) and pd.isna(text)):
            return ""

        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception as exc:  # pragma: no cover - extreme defensive
                logger.error("Failed to convert %s to str: %s", type(text), exc)
                return ""

        try:
            text = text.encode("utf-16", "surrogatepass").decode("utf-16")
            text = unicodedata.normalize("NFKC", text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Unicode normalization failed: %s", exc)

        try:
            text = _SURROGATE_RE.sub(replacement, text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Surrogate removal failed: %s", exc)
            text = "".join(
                ch
                for ch in text
                if not (0xD800 <= ord(ch) <= 0xDFFF)
            )

        text = _CONTROL_RE.sub("", text)
        text = _drop_dangerous_prefix(text)

        try:
            text.encode("utf-8")
        except UnicodeEncodeError as exc:  # pragma: no cover - best effort
            logger.error("Unencodable characters removed: %s", exc)
            text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")

        return text

    # ------------------------------------------------------------------
    @staticmethod
    def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
        """Safely decode ``data`` using ``encoding`` with surrogate handling."""

        try:
            text = data.decode(encoding, errors="surrogatepass")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Primary decode failed: %s", exc)
            try:
                text = data.decode(encoding, errors="ignore")
            except Exception:
                return ""

        return UnicodeProcessor.clean_text(text)

    # ------------------------------------------------------------------
    @staticmethod
    def safe_encode(value: Any) -> str:
        """Convert ``value`` to a safe UTF-8 string."""

        if isinstance(value, bytes):
            return UnicodeProcessor.safe_decode(value)

        return UnicodeProcessor.clean_text(value)

    # ------------------------------------------------------------------
    @staticmethod
    def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Return ``df`` with all columns and object data sanitized."""

        try:
            df_clean = df.copy()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to copy dataframe: %s", exc)
            return df

        new_columns: list[str] = []
        used: set[str] = set()
        for col in df_clean.columns:
            safe_col = UnicodeProcessor.safe_encode(col)
            safe_col = _drop_dangerous_prefix(safe_col) or "col"
            base = safe_col
            count = 1
            while safe_col in used:
                safe_col = f"{base}_{count}"
                count += 1
            used.add(safe_col)
            new_columns.append(safe_col)

        df_clean.columns = new_columns

        obj_cols = df_clean.select_dtypes(include=["object"]).columns
        for col in obj_cols:
            df_clean[col] = (
                df_clean[col]
                .apply(UnicodeProcessor.safe_encode)
                .apply(_drop_dangerous_prefix)
            )

        return df_clean


class ChunkedUnicodeProcessor:
    """Process byte content in manageable chunks."""

    DEFAULT_CHUNK_SIZE: int = 1024 * 1024  # 1MB

    @staticmethod
    def process_large_content(
        content: bytes,
        encoding: str = "utf-8",
        chunk_size: Optional[int] = None,
    ) -> str:
        """Decode and sanitize large byte ``content`` in chunks."""

        if chunk_size is None:
            chunk_size = ChunkedUnicodeProcessor.DEFAULT_CHUNK_SIZE

        parts: list[str] = []
        view = memoryview(content)
        for start in range(0, len(view), chunk_size):
            chunk = view[start : start + chunk_size].tobytes()
            parts.append(UnicodeProcessor.safe_decode(chunk, encoding))
        return "".join(parts)


# ---------------------------------------------------------------------------
# Preferred public API


def clean_unicode_text(text: str) -> str:
    """Clean ``text`` of surrogates, controls and dangerous prefixes."""

    return UnicodeProcessor.clean_text(text)


def safe_decode_bytes(data: bytes, encoding: str = "utf-8") -> str:
    """Decode bytes safely, removing unsafe Unicode characters."""

    return UnicodeProcessor.safe_decode(data, encoding)


def safe_encode_text(value: Any) -> str:
    """Return a UTF-8 safe string representation of ``value``."""

    return UnicodeProcessor.safe_encode(value)


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize a :class:`~pandas.DataFrame` for unsafe Unicode."""

    return UnicodeProcessor.sanitize_dataframe(df)


# ---------------------------------------------------------------------------
# Deprecation helpers


def deprecated(replacement: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to mark legacy helpers as deprecated."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{func.__name__} is deprecated; use {replacement}",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


@deprecated("safe_encode_text")
def safe_unicode_encode(value: Any) -> str:
    return safe_encode_text(value)


@deprecated("safe_encode_text")
def safe_encode(value: Any) -> str:
    return safe_encode_text(value)


@deprecated("safe_decode_bytes")
def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
    return safe_decode_bytes(data, encoding)


@deprecated("clean_unicode_text")
def handle_surrogate_characters(text: str) -> str:
    return UnicodeProcessor.clean_text(text, replacement=UnicodeProcessor.REPLACEMENT_CHAR)


@deprecated("clean_unicode_text")
def clean_unicode_surrogates(text: Any) -> str:
    return clean_unicode_text(str(text))


@deprecated("safe_encode_text")
def sanitize_unicode_input(text: Any) -> str:
    return safe_encode_text(text)


@deprecated("sanitize_dataframe")
def sanitize_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    return sanitize_dataframe(df)


__all__ = [
    # Preferred helpers
    "clean_unicode_text",
    "safe_decode_bytes",
    "safe_encode_text",
    "sanitize_dataframe",
    # Classes
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    # Deprecated
    "safe_unicode_encode",
    "safe_encode",
    "safe_decode",
    "handle_surrogate_characters",
    "clean_unicode_surrogates",
    "sanitize_unicode_input",
    "contains_surrogates",
    "sanitize_data_frame",
]

