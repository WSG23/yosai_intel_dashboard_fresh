"""Consolidated Unicode handling utilities."""

from __future__ import annotations

import logging
import math
import re
import unicodedata
from typing import Any, Callable, Optional, Union


import pandas as pd

logger = logging.getLogger(__name__)

# Precompiled regular expressions used throughout the module
_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")
# Control characters and BOM handling
_CONTROL_RE = re.compile(r"[\x00-\x1F\x7F]")
_BOM_RE = re.compile("\ufeff")
# Leading characters that may trigger dangerous behaviour when interpreted by
# spreadsheet applications (e.g. Excel formula injection)
_DANGEROUS_PREFIX_RE = re.compile(r"^[=+\-@]+")

# Match unpaired surrogate code points (high not followed by low or
# low not preceded by high)
_UNPAIRED_SURROGATE_RE = re.compile(
    r"(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])"
)


def _sanitize_nested(value: Any) -> Any:
    """Recursively sanitize nested data structures."""
    if isinstance(value, dict):
        return {k: _sanitize_nested(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_nested(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_nested(v) for v in value)
    if isinstance(value, set):
        return {_sanitize_nested(v) for v in value}
    return UnicodeProcessor.safe_encode_text(value)


class UnicodeProcessor:
    """Centralized Unicode processing with robust error handling."""

    # Unicode surrogate range constants
    SURROGATE_LOW = 0xD800
    SURROGATE_HIGH = 0xDFFF
    REPLACEMENT_CHAR = "\uFFFD"

    @staticmethod
    def clean_surrogate_chars(text: str, replacement: str = "") -> str:
        """Remove unmatched surrogate characters from ``text``."""
        if not isinstance(text, str):
            text = str(text) if text is not None else ""

        invalid_found = False
        out_chars = []
        i = 0
        try:
            while i < len(text):
                ch = text[i]
                cp = ord(ch)
                # High surrogate
                if 0xD800 <= cp <= 0xDBFF:
                    if i + 1 < len(text) and 0xDC00 <= ord(text[i + 1]) <= 0xDFFF:
                        out_chars.append(ch)
                        out_chars.append(text[i + 1])
                        i += 2
                        continue
                    invalid_found = True
                    if replacement:
                        out_chars.append(replacement)
                    i += 1
                    continue

                # Low surrogate without preceding high surrogate
                if 0xDC00 <= cp <= 0xDFFF:
                    invalid_found = True
                    if replacement:
                        out_chars.append(replacement)
                    i += 1
                    continue

                out_chars.append(ch)
                i += 1

            cleaned = "".join(out_chars)

            if invalid_found:
                logger.warning("Invalid surrogate sequence removed")

            cleaned = unicodedata.normalize("NFKC", cleaned)
            cleaned = _CONTROL_RE.sub("", cleaned)
            return cleaned
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Failed to clean surrogate chars: {exc}")
            return "".join(
                ch
                for ch in text
                if not (
                    UnicodeProcessor.SURROGATE_LOW <= ord(ch) <= UnicodeProcessor.SURROGATE_HIGH
                )
            )

    @staticmethod
    def safe_decode_bytes(data: bytes, encoding: str = "utf-8") -> str:
        """Safely decode bytes with Unicode surrogate handling."""
        try:
            text = data.decode(encoding, errors="surrogatepass")
            return UnicodeProcessor.clean_surrogate_chars(text)
        except UnicodeDecodeError:
            try:
                text = data.decode(encoding, errors="replace")
                return UnicodeProcessor.clean_surrogate_chars(text)
            except Exception:
                return data.decode(encoding, errors="ignore")

    @staticmethod
    def safe_encode_text(value: Any) -> str:
        """Convert any value to a safe UTF-8 string."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""

        try:
            if isinstance(value, bytes):
                return UnicodeProcessor.safe_decode_bytes(value)

            text = str(value)
            cleaned = UnicodeProcessor.clean_surrogate_chars(text)
            cleaned.encode("utf-8")
            return cleaned
        except Exception as exc:  # pragma: no cover - best effort
            logger.error(f"Unicode encoding failed for {type(value)}: {exc}")
            return "".join(ch for ch in str(value) if ord(ch) < 128)

    @staticmethod
    def sanitize_dataframe(
        df: pd.DataFrame,
        *,
        progress: Union[bool, Callable[[int, int], None], None] = None,
    ) -> pd.DataFrame:
        """Sanitize entire DataFrame for Unicode issues.

        Parameters
        ----------
        df:
            DataFrame to sanitize.
        progress:
            If ``True`` and the DataFrame has over 10k rows, progress will be
            logged with :func:`logging.info` for each processed column. If a
            callable is provided it will be invoked with ``(column_index,
            total_columns)`` for every sanitized column.
        """
        try:
            df_clean = df.copy()

            new_columns = []
            for col in df_clean.columns:
                safe_col = UnicodeProcessor.safe_encode_text(col)
                safe_col = _DANGEROUS_PREFIX_RE.sub("", safe_col)
                new_columns.append(safe_col or f"col_{len(new_columns)}")

            df_clean.columns = new_columns

            for col in df_clean.select_dtypes(include=["object"]).columns:
                df_clean[col] = df_clean[col].apply(_sanitize_nested)

                df_clean[col] = df_clean[col].apply(
                    lambda x: _DANGEROUS_PREFIX_RE.sub("", x)
                    if isinstance(x, str)
                    else x
                )

                if callable(progress):
                    progress(idx + 1, total_cols)
                elif progress and len(df_clean) > 10_000:
                    logger.info("Sanitized column %s/%s", idx + 1, total_cols)

            return df_clean
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"DataFrame sanitization failed: {exc}")
            return df


class ChunkedUnicodeProcessor:
    """Process large files in chunks to handle memory efficiently."""

    DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1MB

    @staticmethod
    def process_large_content(
        content: bytes,
        encoding: str = "utf-8",
        chunk_size: Optional[int] = None,
    ) -> str:
        """Process large byte content in chunks with Unicode handling."""

        if chunk_size is None:
            chunk_size = ChunkedUnicodeProcessor.DEFAULT_CHUNK_SIZE

        try:
            pieces = []
            view = memoryview(content)

            for start in range(0, len(view), chunk_size):
                chunk = view[start : start + chunk_size].tobytes()
                text_chunk = UnicodeProcessor.safe_decode_bytes(chunk, encoding)
                pieces.append(text_chunk)

            return "".join(pieces)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Chunked processing failed: {exc}")
            return UnicodeProcessor.safe_decode_bytes(content, encoding)


# Public API
def clean_unicode_text(text: str) -> str:
    """Clean Unicode text of surrogate characters."""

    return UnicodeProcessor.clean_surrogate_chars(text)


def safe_decode_bytes(data: bytes, encoding: str = "utf-8") -> str:
    """Safely decode bytes with Unicode handling."""

    return UnicodeProcessor.safe_decode_bytes(data, encoding)


def safe_encode_text(value: Any) -> str:
    """Convert any value to a safe UTF-8 string."""

    return UnicodeProcessor.safe_encode_text(value)


def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
    """Safely decode bytes with Unicode handling."""

    return UnicodeProcessor.safe_decode_bytes(data, encoding)


def safe_encode(value: Any) -> str:
    """Convert any value to a safe UTF-8 string."""

    return UnicodeProcessor.safe_encode_text(value)


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize DataFrame for Unicode issues."""

    return UnicodeProcessor.sanitize_dataframe(df)


def sanitize_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Deprecated alias for :func:`sanitize_dataframe`."""

    return sanitize_dataframe(df)




# ---------------------------------------------------------------------------
# Backwards compatibility helpers

def handle_surrogate_characters(text: str) -> str:
    """Return text with surrogate characters replaced by ``REPLACEMENT_CHAR``."""

    return UnicodeProcessor.clean_surrogate_chars(
        text, UnicodeProcessor.REPLACEMENT_CHAR
    )


def safe_unicode_encode(value: Any) -> str:
    """Alias for :func:`safe_encode`."""

    return safe_encode(value)


def clean_unicode_surrogates(text: Any) -> str:
    """Remove surrogate characters from ``text``."""

    return UnicodeProcessor.clean_surrogate_chars(str(text))


def contains_surrogates(text: str) -> bool:
    """Return ``True`` if ``text`` contains any unpaired surrogate code points."""

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:  # pragma: no cover - defensive
            return False

    return bool(_UNPAIRED_SURROGATE_RE.search(text))


def sanitize_unicode_input(text: Union[str, Any]) -> str:
    """Return ``text`` stripped of surrogate pairs and BOM characters."""

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to convert %r to str: %s", text, exc)
            return ""

    try:
        cleaned = _SURROGATE_RE.sub("", text)
        cleaned = _BOM_RE.sub("", cleaned)
        return cleaned
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("sanitize_unicode_input failed: %s", exc)
        return "".join(ch for ch in str(text) if ch.isascii())


def process_large_csv_content(
    content: bytes,
    encoding: str = "utf-8",
    *,
    chunk_size: int = ChunkedUnicodeProcessor.DEFAULT_CHUNK_SIZE,
) -> str:
    """Decode potentially large CSV content in chunks and sanitize."""

    return ChunkedUnicodeProcessor.process_large_content(content, encoding, chunk_size)


def safe_format_number(value: Union[int, float]) -> Optional[str]:
    """Return formatted number or ``None`` for NaN/inf values."""

    try:
        if isinstance(value, bool):
            value = int(value)
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            return f"{value:,}"
    except (ValueError, TypeError) as exc:  # pragma: no cover - defensive
        logger.warning("Failed to format number %r: %s", value, exc)
    return None


__all__ = [
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    "clean_unicode_text",
    "safe_decode_bytes",
    "safe_encode_text",
    "safe_decode",
    "safe_encode",
    "sanitize_dataframe",
    "sanitize_data_frame",
    # Backwards compatible aliases
    "safe_unicode_encode",
    "handle_surrogate_characters",
    "clean_unicode_surrogates",
    "sanitize_unicode_input",
    "contains_surrogates",
    "process_large_csv_content",
    "safe_format_number",
]
