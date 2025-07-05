"""Consolidated Unicode handling utilities."""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any, Union, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Regular expression matching ASCII control characters to be stripped.

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class UnicodeProcessor:
    """Centralized Unicode processing with robust error handling."""

    # Unicode surrogate range constants
    SURROGATE_LOW = 0xD800
    SURROGATE_HIGH = 0xDFFF
    REPLACEMENT_CHAR = "\uFFFD"

    @staticmethod
    def clean_surrogate_chars(text: str, replacement: str = "") -> str:
        """Remove Unicode surrogate characters from ``text``."""
        if not isinstance(text, str):
            text = str(text) if text is not None else ""

        try:
            cleaned = re.sub(r"[\uD800-\uDFFF]", replacement, text)
            cleaned = _CONTROL_RE.sub("", cleaned)
            cleaned = unicodedata.normalize("NFKC", cleaned)
            cleaned = _CONTROL_RE.sub("", cleaned)
            return cleaned
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Failed to clean surrogate chars: {exc}")
            return "".join(
                ch
                for ch in text
                if not (UnicodeProcessor.SURROGATE_LOW <= ord(ch) <= UnicodeProcessor.SURROGATE_HIGH)
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
    def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize entire DataFrame for Unicode issues."""
        try:
            df_clean = df.copy()

            new_columns = []
            for col in df_clean.columns:
                safe_col = UnicodeProcessor.safe_encode_text(col)
                safe_col = re.sub(r"^[=+\-@]+", "", safe_col)
                new_columns.append(safe_col or f"col_{len(new_columns)}")

            df_clean.columns = new_columns

            for col in df_clean.select_dtypes(include=["object"]).columns:
                df_clean[col] = df_clean[col].apply(lambda x: UnicodeProcessor.safe_encode_text(x))
                df_clean[col] = df_clean[col].apply(
                    lambda x: re.sub(r"^[=+\-@]+", "", x) if isinstance(x, str) else x
                )

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

    return UnicodeProcessor.clean_surrogate_chars(text, UnicodeProcessor.REPLACEMENT_CHAR)


def safe_unicode_encode(value: Any) -> str:
    """Alias for :func:`safe_encode`."""

    return safe_encode(value)


def clean_unicode_surrogates(text: Any) -> str:
    """Remove surrogate characters from ``text``."""

    return UnicodeProcessor.clean_surrogate_chars(str(text))


def sanitize_unicode_input(text: Union[str, Any], replacement: str = UnicodeProcessor.REPLACEMENT_CHAR) -> str:
    """Sanitize text input to handle Unicode and control characters."""

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:  # pragma: no cover - defensive
            logger.warning("Failed to convert %r to str", text, exc_info=True)
            return ""

    try:
        cleaned = UnicodeProcessor.clean_surrogate_chars(text, replacement)
        cleaned.encode("utf-8")
        return cleaned
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("sanitize_unicode_input failed: %s", exc)
        return "".join(ch for ch in str(text) if ch.isascii())


def process_large_csv_content(
    content: bytes, encoding: str = "utf-8", *, chunk_size: int = ChunkedUnicodeProcessor.DEFAULT_CHUNK_SIZE
) -> str:
    """Decode potentially large CSV content in chunks and sanitize."""

    return ChunkedUnicodeProcessor.process_large_content(content, encoding, chunk_size)


def safe_format_number(value: Union[int, float], default: str = "0") -> str:
    """Safely format numbers with Unicode safety."""

    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f"{value:,}"
        return default
    except (ValueError, TypeError):  # pragma: no cover - defensive
        return default


__all__ = [
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    "clean_unicode_text",
    "safe_decode",
    "safe_encode",
    "sanitize_dataframe",
    "sanitize_data_frame",
    # Backwards compatible aliases
    "safe_unicode_encode",
    "handle_surrogate_characters",
    "clean_unicode_surrogates",
    "sanitize_unicode_input",
    "process_large_csv_content",
    "safe_format_number",
]

