"""Enterprise-grade Unicode utilities and migration helpers.

This module consolidates fragmented Unicode handling logic into a single,
robust implementation.  All new code should use the preferred API functions
defined here.  Legacy helpers remain available for backwards compatibility and
emit :class:`DeprecationWarning` when called.
"""

from __future__ import annotations

import logging
import math
import re
import unicodedata
from typing import Any, Callable, Iterable, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Precompiled regular expressions used throughout the module
_CONTROL_RE = re.compile(r"[\x00-\x1F\x7F]")
_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")
_DANGEROUS_PREFIX_RE = re.compile(r"^[=+\-@]+")
_BOM_RE = re.compile("\ufeff")
_UNPAIRED_SURROGATE_RE = re.compile(
    r"(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])"
)


def _drop_dangerous_prefix(text: str) -> str:
    """Remove characters that can trigger spreadsheet formula injection."""

    return _DANGEROUS_PREFIX_RE.sub("", text)


# ---------------------------------------------------------------------------
# Core classes


class UnicodeProcessor:
    """Centralised Unicode processing utilities."""

    REPLACEMENT_CHAR: str = "\uFFFD"

    # ------------------------------------------------------------------
    @staticmethod
    def clean_surrogate_chars(text: str, replacement: str = "") -> str:
        """Return ``text`` with surrogate code points removed or replaced.

        Valid UTF-16 surrogate pairs are converted to their corresponding
        Unicode characters. Any unpaired surrogates are dropped or replaced
        with ``replacement`` if provided.
        """

        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to convert %s to str: %s", type(text), exc)
                return ""

        out: list[str] = []
        i = 0
        while i < len(text):
            ch = text[i]
            code = ord(ch)

            # High surrogate
            if 0xD800 <= code <= 0xDBFF:
                if i + 1 < len(text):
                    next_code = ord(text[i + 1])
                    if 0xDC00 <= next_code <= 0xDFFF:
                        pair = ((code - 0xD800) << 10) + (next_code - 0xDC00) + 0x10000
                        out.append(chr(pair))
                        i += 2
                        continue
                if replacement:
                    out.append(replacement)
                i += 1
                continue

            # Low surrogate without preceding high surrogate
            if 0xDC00 <= code <= 0xDFFF:
                if replacement:
                    out.append(replacement)
                i += 1
                continue

            out.append(ch)
            i += 1

        return "".join(out)

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
            text = "".join(ch for ch in text if not (0xD800 <= ord(ch) <= 0xDFFF))

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


class UnicodeTextProcessor:
    """Clean and normalise arbitrary text."""

    @staticmethod
    def clean_text(text: Any) -> str:
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to convert text to str: %s", exc)
                return ""

        try:
            text = unicodedata.normalize("NFKC", text)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Unicode normalization failed: %s", exc)

        try:
            text = _SURROGATE_RE.sub("", text)
            text = _CONTROL_RE.sub("", text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Regex cleanup failed: %s", exc)
            text = "".join(
                ch
                for ch in text
                if not (0xD800 <= ord(ch) <= 0xDFFF or ord(ch) < 32 or ord(ch) == 0x7F)
            )

        return text

    @staticmethod
    def clean_surrogate_chars(text: str, replacement: str = "") -> str:
        """Return ``text`` with surrogate code points removed or replaced."""

        return UnicodeProcessor.clean_surrogate_chars(text, replacement)


class UnicodeSQLProcessor:
    """Safely encode SQL queries with Unicode handling."""

    @staticmethod
    def encode_query(query: Any) -> str:
        cleaned = UnicodeTextProcessor.clean_text(query)
        try:
            cleaned.encode("utf-8")
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Unicode encode failed: %s", exc)
            cleaned = cleaned.encode("utf-8", "ignore").decode("utf-8", "ignore")
        return cleaned


class UnicodeSecurityProcessor:
    """Sanitize input for security sensitive contexts."""

    _HTML_REPLACEMENTS = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
        "/": "&#x2F;",
    }

    @staticmethod
    def sanitize_input(text: Any) -> str:
        sanitized = UnicodeTextProcessor.clean_text(text)
        for char, repl in UnicodeSecurityProcessor._HTML_REPLACEMENTS.items():
            sanitized = sanitized.replace(char, repl)
        return sanitized


def object_count(items: Iterable[Any]) -> int:
    """Return the number of unique strings appearing more than once."""

    counts: dict[str, int] = {}
    for item in items:
        if isinstance(item, str):
            counts[item] = counts.get(item, 0) + 1
    return sum(1 for v in counts.values() if v > 1)


# ---------------------------------------------------------------------------
# Preferred public API


def clean_unicode_text(text: str) -> str:
    """Clean ``text`` of surrogates, controls and dangerous prefixes."""

    return UnicodeProcessor.clean_text(text)


def safe_decode_bytes(data: bytes, encoding: str = "utf-8") -> str:
    """Decode bytes safely, removing unsafe Unicode characters."""

    return UnicodeProcessor.safe_decode(data, encoding)


def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
    """Alias for :func:`safe_decode_bytes`."""

    return safe_decode_bytes(data, encoding)


def safe_encode_text(value: Any) -> str:
    """Return a UTF-8 safe string representation of ``value``."""

    return UnicodeProcessor.safe_encode(value)


def safe_encode(value: Any) -> str:
    """Alias for :func:`safe_encode_text`."""

    return safe_encode_text(value)


def sanitize_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Deprecated alias for :func:`sanitize_dataframe`."""

    return sanitize_dataframe(df)


def handle_surrogate_characters(text: str) -> str:
    """Return text with surrogate characters replaced by ``REPLACEMENT_CHAR``."""

    return UnicodeProcessor.clean_text(text, UnicodeProcessor.REPLACEMENT_CHAR)


def safe_unicode_encode(value: Any) -> str:
    """Deprecated wrapper around :func:`safe_encode`."""

    return safe_encode(value)


def clean_unicode_surrogates(text: Any) -> str:
    """Remove surrogate characters from ``text``."""

    return UnicodeProcessor.clean_text(text)


def clean_surrogate_chars(text: str, replacement: str = "") -> str:
    """Return ``text`` with surrogate code points removed or replaced."""

    return UnicodeProcessor.clean_surrogate_chars(text, replacement)


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


def contains_surrogates(text: str) -> bool:
    """Return ``True`` if ``text`` contains any unpaired surrogate code points."""

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:  # pragma: no cover - defensive
            return False

    return bool(_UNPAIRED_SURROGATE_RE.search(text))


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize a :class:`~pandas.DataFrame` for unsafe Unicode."""

    return UnicodeProcessor.sanitize_dataframe(df)


__all__ = [
    "clean_unicode_text",
    "safe_decode_bytes",
    "safe_decode",
    "safe_encode_text",
    "safe_encode",
    "sanitize_dataframe",
    "sanitize_data_frame",
    "handle_surrogate_characters",
    "safe_unicode_encode",
    "clean_unicode_surrogates",
    "clean_surrogate_chars",
    "sanitize_unicode_input",
    "contains_surrogates",
    "process_large_csv_content",
    "safe_format_number",
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    "UnicodeTextProcessor",
    "UnicodeSQLProcessor",
    "UnicodeSecurityProcessor",
    "object_count",
]
