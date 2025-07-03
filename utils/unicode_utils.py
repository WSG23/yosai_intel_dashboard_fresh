from __future__ import annotations

"""Unified Unicode helper functions."""

import logging
import re
import unicodedata
from typing import Any, Union

import pandas as pd

logger = logging.getLogger(__name__)


def handle_surrogate_characters(text: str) -> str:
    """Return ``text`` with problematic surrogate characters sanitized."""
    try:
        cleaned = re.sub(r"[\uD800-\uDFFF]", "\uFFFD", text)
        cleaned = unicodedata.normalize("NFKC", cleaned)
        return cleaned.encode("utf-8", "replace").decode("utf-8")
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Surrogate character handling failed: %s", exc)
        return text.encode("utf-8", "replace").decode("utf-8")


def safe_unicode_encode(value: Any) -> str:
    """Convert ``value`` to a UTF-8 string, removing invalid surrogates."""
    try:
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8", "surrogatepass")
            except Exception:
                value = value.decode("latin-1", "surrogatepass")
        else:
            value = str(value)
        value = re.sub(r"[\ud800-\udfff]", "", value)
        return value.encode("utf-8", "ignore").decode("utf-8", "ignore")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Unicode encoding failed: %s", exc)
        return handle_surrogate_characters(str(value))


def clean_unicode_surrogates(text: Any) -> str:
    """Remove Unicode surrogate characters from ``text``."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    text = str(text)
    text = re.sub(r"[\ud800-\udfff]", "", text)
    text = text.replace("\ufffe", "").replace("\uffff", "")
    return text


def sanitize_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize DataFrame column names and string values."""
    df_clean = df.copy()

    new_columns = []
    for col in df_clean.columns:
        safe_col = clean_unicode_surrogates(col)
        safe_col = re.sub(r"^[=+\-@]+", "", safe_col)
        new_columns.append(safe_col)
    df_clean.columns = new_columns

    for col in df_clean.select_dtypes(include=["object"]).columns:
        df_clean[col] = df_clean[col].map(clean_unicode_surrogates)
        df_clean[col] = df_clean[col].map(lambda x: re.sub(r"^[=+\-@]+", "", x))

    return df_clean


def sanitize_unicode_input(text: Union[str, Any], replacement: str = "\ufffd") -> str:
    """Sanitize text input to handle Unicode surrogate characters."""
    if text is None:
        return ""

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return ""

    try:
        cleaned = text.encode("utf-8", errors="ignore").decode("utf-8")
        cleaned = unicodedata.normalize("NFKC", cleaned)
        cleaned = "".join(
            char for char in cleaned
            if unicodedata.category(char)[0] != "C" or char in "\t\n\r"
        )
        cleaned = re.sub(r"[\ud800-\udfff]", replacement, cleaned)
        return cleaned
    except Exception:
        return "".join(char for char in str(text) if ord(char) < 127)


def process_large_csv_content(content: bytes, encoding: str = "utf-8", *, chunk_size: int = 1024 * 1024) -> str:
    """Decode potentially large CSV content in chunks and sanitize."""
    pieces: list[str] = []
    mv = memoryview(content)
    for start in range(0, len(mv), chunk_size):
        chunk = mv[start : start + chunk_size].tobytes()
        text = chunk.decode(encoding, errors="surrogatepass")
        pieces.append(clean_unicode_surrogates(text))
    return "".join(pieces)


def safe_format_number(value: Union[int, float], default: str = "0") -> str:
    """Safely format numbers with Unicode safety."""
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f"{value:,}"
        return default
    except (ValueError, TypeError):
        return default


__all__ = [
    "safe_unicode_encode",
    "handle_surrogate_characters",
    "clean_unicode_surrogates",
    "sanitize_data_frame",
    "sanitize_unicode_input",
    "process_large_csv_content",
    "safe_format_number",
]
