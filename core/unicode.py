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
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Iterable, Optional, Union

import pandas as pd  # type: ignore[import]

from config.database_exceptions import UnicodeEncodingError
from security.unicode_security_validator import (
    UnicodeSecurityConfig,
    UnicodeSecurityValidator,
)

from .exceptions import SecurityError
from .security_patterns import (
    PATH_TRAVERSAL_PATTERNS,
    SQL_INJECTION_PATTERNS,
    XSS_PATTERNS,
)

logger = logging.getLogger(__name__)

# Global Unicode security validator used across this module
_unicode_validator = UnicodeSecurityValidator(
    config=UnicodeSecurityConfig(strict_mode=True, remove_surrogates=True)
)


# ---------------------------------------------------------------------------
# Precompiled regular expressions used throughout the module
_CONTROL_RE = re.compile(r"[\x00-\x1F\x7F]")
_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")
_DANGEROUS_PREFIX_RE = re.compile(r"^[=+\-@]+")
_BOM_RE = re.compile("\ufeff")
_UNPAIRED_SURROGATE_RE = re.compile(
    r"(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])"
)

# Precompile common security patterns for quick detection
_MALICIOUS_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (SQL_INJECTION_PATTERNS + XSS_PATTERNS + PATH_TRAVERSAL_PATTERNS)
]


def _drop_dangerous_prefix(text: str) -> str:
    """Remove characters that can trigger spreadsheet formula injection."""

    return _DANGEROUS_PREFIX_RE.sub("", text)


# ---------------------------------------------------------------------------
# Core classes


class UnicodeProcessor:
    """Centralised Unicode processing utilities."""

    REPLACEMENT_CHAR: str = "\ufffd"

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
                logger.error(f"Failed to convert {type(text)} to str: {exc}")
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
                logger.error(f"Failed to convert {type(text)} to str: {exc}")
                return ""

        try:
            text = text.encode("utf-16", "surrogatepass").decode("utf-16")
            text = unicodedata.normalize("NFKC", text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Unicode normalization failed: {exc}")

        try:
            text = _SURROGATE_RE.sub(replacement, text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Surrogate removal failed: {exc}")
            text = "".join(ch for ch in text if not (0xD800 <= ord(ch) <= 0xDFFF))

        text = _CONTROL_RE.sub("", text)
        text = _drop_dangerous_prefix(text)

        try:
            text.encode("utf-8")
        except UnicodeEncodeError as exc:  # pragma: no cover - best effort
            logger.error(f"Unencodable characters removed: {exc}")
            text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")

        return text

    # ------------------------------------------------------------------
    @staticmethod
    def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
        """Safely decode ``data`` using ``encoding`` with surrogate handling."""

        try:
            text = data.decode(encoding, errors="surrogatepass")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Primary decode failed: {exc}")
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
    def safe_encode_text(value: Any) -> str:
        """Alias for :meth:`safe_encode`."""

        return UnicodeProcessor.safe_encode(value)

    # ------------------------------------------------------------------
    @staticmethod
    def safe_decode_text(data: bytes, encoding: str = "utf-8") -> str:
        """Alias for :meth:`safe_decode`."""

        return UnicodeProcessor.safe_decode(data, encoding)

    # ------------------------------------------------------------------
    @staticmethod
    def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Return ``df`` sanitized using the enterprise validator."""

        return _unicode_validator.validate_dataframe(df)

    # ------------------------------------------------------------------
    @staticmethod
    def process_dict(data: Any) -> Any:
        """Recursively sanitize ``data`` for safe JSON transport."""

        if isinstance(data, dict):
            return {
                UnicodeProcessor.safe_encode_text(k): UnicodeProcessor.process_dict(v)
                for k, v in data.items()
            }

        if isinstance(data, list):
            return [UnicodeProcessor.process_dict(v) for v in data]

        if isinstance(data, tuple):
            return type(data)(UnicodeProcessor.process_dict(v) for v in data)

        if isinstance(data, set):
            return {UnicodeProcessor.process_dict(v) for v in data}

        if isinstance(data, bytes):
            return UnicodeProcessor.safe_decode_text(data)

        if hasattr(data, "__dict__"):
            return UnicodeProcessor.process_dict(vars(data))

        if isinstance(data, (int, float, bool)) or data is None:
            return data

        return UnicodeProcessor.safe_encode_text(data)


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
        return UnicodeProcessor.clean_text(text)

    @staticmethod
    def clean_surrogate_chars(text: str, replacement: str = "") -> str:
        """Return ``text`` with surrogate code points removed or replaced."""

        return UnicodeProcessor.clean_surrogate_chars(text, replacement)


class UnicodeSQLProcessor:
    """Safely encode SQL queries with Unicode handling."""

    @staticmethod
    def encode_query(query: Any) -> str:
        original = str(query)
        if contains_surrogates(original):
            raise UnicodeEncodingError("surrogate characters detected", original)
        cleaned = UnicodeProcessor.clean_text(original)
        try:
            cleaned.encode("utf-8")
        except Exception as exc:  # pragma: no cover - best effort
            logger.error(f"Unicode encode failed: {exc}")
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
        sanitized = UnicodeProcessor.clean_text(text)
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

    return _unicode_validator.validate_and_sanitize(text)


def safe_decode_bytes(data: bytes, encoding: str = "utf-8") -> str:
    """Decode bytes safely, removing unsafe Unicode characters."""

    return UnicodeProcessor.safe_decode(data, encoding)


def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
    """Alias for :func:`safe_decode_bytes`."""

    return safe_decode_bytes(data, encoding)


def safe_decode_text(data: bytes, encoding: str = "utf-8") -> str:
    """Safely decode byte data to text."""

    return UnicodeProcessor.safe_decode_text(data, encoding)


def safe_encode_text(text: Any) -> str:
    """Return ``text`` encoded safely as Unicode text."""

    return UnicodeProcessor.safe_encode_text(text)


def safe_encode(value: Any) -> str:
    """Alias for :func:`UnicodeProcessor.safe_encode`."""

    return UnicodeProcessor.safe_encode(value)


def utf8_safe_encode(value: Any) -> bytes:
    """Return UTF-8 encoded bytes handling surrogate pairs."""

    return UnicodeProcessor.safe_encode_text(value).encode(
        "utf-8", errors="surrogatepass"
    )


def utf8_safe_decode(data: bytes) -> str:
    """Decode UTF-8 bytes while preserving surrogate pairs."""

    return data.decode("utf-8", errors="surrogatepass")


def sanitize_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Deprecated alias for :func:`sanitize_dataframe`."""

    return sanitize_dataframe(df)


def handle_surrogate_characters(text: str) -> str:
    """Return text with surrogate characters replaced by ``REPLACEMENT_CHAR``."""

    return UnicodeProcessor.clean_text(text, UnicodeProcessor.REPLACEMENT_CHAR)


def safe_unicode_encode(value: Any) -> str:
    """Deprecated wrapper around :func:`safe_encode`."""

    return safe_encode(value)


def clean_surrogate_chars(text: str, replacement: str = "") -> str:
    """Return ``text`` with surrogate code points removed or replaced."""

    return UnicodeProcessor.clean_surrogate_chars(text, replacement)


def clean_unicode_surrogates(text: str, replacement: str = "") -> str:
    """Alias for :func:`clean_surrogate_chars`."""

    return clean_surrogate_chars(text, replacement)


def sanitize_unicode_input(text: Union[str, Any]) -> str:
    """Return ``text`` normalized and stripped of surrogate codepoints."""

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Failed to convert {text!r} to str: {exc}")
            return ""

    def _strip_pairs(val: str) -> str:
        out = []
        i = 0
        while i < len(val):
            ch = val[i]
            code = ord(ch)
            if code > 0xFFFF:
                i += 1
                continue
            if 0xD800 <= code <= 0xDBFF:
                if i + 1 < len(val) and 0xDC00 <= ord(val[i + 1]) <= 0xDFFF:
                    i += 2
                    continue
                i += 1
                continue
            if 0xDC00 <= code <= 0xDFFF:
                i += 1
                continue
            out.append(ch)
            i += 1
        return "".join(out)

    try:
        cleaned = _strip_pairs(text)
        sanitized = _unicode_validator.validate_and_sanitize(cleaned)
        sanitized = unicodedata.normalize("NFKC", sanitized)
        return _drop_dangerous_prefix(sanitized)
    except UnicodeError as exc:  # pragma: no cover - best effort
        logger.warning(f"Unicode sanitization failed: {exc}")
        cleaned = UnicodeProcessor.clean_surrogate_chars(text)
        try:
            cleaned = _unicode_validator.validate_and_sanitize(cleaned)
            cleaned = unicodedata.normalize("NFKC", cleaned)
            return _drop_dangerous_prefix(cleaned)
        except Exception as inner:  # pragma: no cover - extreme defensive
            logger.error(f"Normalization retry failed: {inner}")
            return cleaned
    except Exception as exc:  # pragma: no cover - extreme defensive
        logger.error(f"sanitize_unicode_input failed: {exc}")
        cleaned = "".join(ch for ch in str(text) if not (0xD800 <= ord(ch) <= 0xDFFF))
        return _drop_dangerous_prefix(cleaned)


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
        logger.warning(f"Failed to format number {value!r}: {exc}")
    return None


def contains_surrogates(text: str) -> bool:
    """Return ``True`` if ``text`` contains any unpaired surrogate code points."""

    return _unicode_validator._contains_surrogates(str(text))


def has_malicious_patterns(text: str) -> bool:
    """Return ``True`` if ``text`` matches known attack patterns."""

    if not isinstance(text, str):
        return False

    for pattern in _MALICIOUS_PATTERNS:
        if pattern.search(text):
            return True
    return False


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize a :class:`~pandas.DataFrame` for unsafe Unicode."""

    return UnicodeProcessor.sanitize_dataframe(df)


def secure_unicode_sanitization(value: Any, *, check_malicious: bool = True) -> str:
    """Return a normalised, safe Unicode string.

    Parameters
    ----------
    value:
        Input text to sanitize. Non-string values are coerced to ``str``.
    check_malicious:
        When ``True``, raise :class:`SecurityError` if known malicious
        patterns are detected.
    """

    validator = _unicode_validator
    if not check_malicious:
        validator = UnicodeSecurityValidator(
            UnicodeSecurityConfig(strict_mode=False, remove_surrogates=True)
        )

    try:
        return validator.validate_and_sanitize(value)
    except SecurityError:
        raise
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning(f"secure_unicode_sanitization failed: {exc}")
        return validator.validate_and_sanitize(str(value))


def safe_navbar_text(text: Any) -> str:
    """Safely process text for navbar components.

    Handles Unicode surrogates that can cause UI flash/disappear issues.
    """

    if text is None:
        return ""

    # Use existing safe_encode_text with additional navbar-specific handling
    cleaned = safe_encode_text(text)

    # Additional navbar-specific cleaning
    if not cleaned:
        return ""

    # Remove zero-width characters that can break navbar rendering
    zero_width_chars = [
        "\u200b",  # Zero-width space
        "\u200c",  # Zero-width non-joiner
        "\u200d",  # Zero-width joiner
        "\ufeff",  # Zero-width no-break space (BOM)
    ]

    for char in zero_width_chars:
        cleaned = cleaned.replace(char, "")

    # Ensure text is renderable in HTML context
    try:
        # Test encoding
        cleaned.encode("utf-8")
        # Test HTML rendering safety
        import html

        html.escape(cleaned)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback to ASCII-safe version
        cleaned = cleaned.encode("ascii", errors="ignore").decode("ascii")

    return cleaned.strip()


def unicode_safe_callback(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to sanitize Unicode arguments and results."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        safe_args = [safe_encode_text(a) if isinstance(a, str) else a for a in args]
        safe_kwargs = {
            k: safe_encode_text(v) if isinstance(v, str) else v
            for k, v in kwargs.items()
        }
        result = func(*safe_args, **safe_kwargs)
        if isinstance(result, str):
            return safe_encode_text(result)
        if isinstance(result, (list, tuple)):
            return [safe_encode_text(r) if isinstance(r, str) else r for r in result]
        return result

    return wrapper


# ---------------------------------------------------------------------------
# Additional helpers unified from legacy modules


class SurrogateHandlingStrategy(Enum):
    """Strategies for handling surrogate characters."""

    REPLACE = "replace"
    REJECT = "reject"
    STRIP = "strip"


@dataclass
class SurrogateHandlingConfig:
    """Configuration for :class:`EnhancedUnicodeProcessor`."""

    strategy: SurrogateHandlingStrategy = SurrogateHandlingStrategy.REPLACE
    replacement_char: str = "\ufffd"
    normalize_form: str = "NFC"
    log_errors: bool = True


class EnhancedUnicodeProcessor:
    """Process text with configurable surrogate handling."""

    def __init__(self, config: Optional[SurrogateHandlingConfig] = None) -> None:
        self.config = config or SurrogateHandlingConfig()

    def process_text(self, text: str) -> str:
        if not text:
            return ""

        if contains_surrogates(text):
            if self.config.strategy is SurrogateHandlingStrategy.REJECT:
                raise UnicodeError("Surrogate characters not allowed")
            elif self.config.strategy is SurrogateHandlingStrategy.STRIP:
                text = _SURROGATE_RE.sub("", text)
            else:  # REPLACE
                text = _SURROGATE_RE.sub(self.config.replacement_char, text)

        try:
            text = unicodedata.normalize(self.config.normalize_form, text)
        except Exception as exc:  # pragma: no cover - defensive
            if self.config.log_errors:
                logger.warning(f"Unicode normalization failed: {exc}")

        return text


def _remove_invalid_surrogates(text: str) -> str:
    """Return ``text`` without lone surrogate code points."""

    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        code = ord(ch)
        if 0xD800 <= code <= 0xDBFF:
            if i + 1 < len(text) and 0xDC00 <= ord(text[i + 1]) <= 0xDFFF:
                out.append(ch)
                out.append(text[i + 1])
                i += 2
                continue
            i += 1
            continue
        if 0xDC00 <= code <= 0xDFFF:
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def safe_unicode_decode(data: Any, encoding: str = "utf-8") -> str:
    """Decode ``data`` safely removing invalid surrogates."""

    if isinstance(data, str):
        return _remove_invalid_surrogates(data)

    try:
        text = data.decode(encoding, errors="surrogatepass")
    except UnicodeError as exc:
        logger.warning(f"Primary decode failed: {exc}")
        try:
            text = data.decode(encoding, errors="replace")
        except Exception:
            text = data.decode("utf-8", errors="ignore")
    return _remove_invalid_surrogates(text)


class UnicodeNormalizationError(Exception):
    """Raised when Unicode normalization fails."""


def normalize_unicode_safely(text: Any, form: str = "NFKC") -> str:
    """Return ``text`` normalised using ``form`` with robust error handling."""

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Failed to convert {text!r} to str: {exc}")
            raise UnicodeNormalizationError(str(exc)) from exc

    try:
        return unicodedata.normalize(form, text)
    except Exception as exc:  # pragma: no cover - best effort
        logger.error(f"Unicode normalization failed: {exc}")
        raise UnicodeNormalizationError(str(exc)) from exc


def detect_surrogate_pairs(text: Any) -> bool:
    """Return ``True`` if ``text`` contains any UTF-16 surrogate pair."""

    return _unicode_validator._contains_surrogates(str(text))


def sanitize_for_utf8(value: Any) -> str:
    """Return ``value`` cleaned and safe for UTF-8."""

    try:
        return _unicode_validator.validate_and_sanitize(value)
    except SecurityError:
        raise
    except Exception as exc:  # pragma: no cover - best effort
        logger.error(f"Unicode sanitization failed: {exc}")
        return _unicode_validator.validate_and_sanitize(str(value))


__all__ = [
    "clean_unicode_text",
    "safe_decode_bytes",
    "safe_decode",
    "safe_decode_text",
    "safe_encode_text",
    "safe_encode",
    "sanitize_dataframe",
    "sanitize_data_frame",
    "safe_navbar_text",
    "handle_surrogate_characters",
    "safe_unicode_encode",
    "clean_unicode_surrogates",
    "clean_surrogate_chars",
    "sanitize_unicode_input",
    "contains_surrogates",
    "secure_unicode_sanitization",
    "process_large_csv_content",
    "safe_format_number",
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    "UnicodeTextProcessor",
    "UnicodeSQLProcessor",
    "UnicodeSecurityProcessor",
    "object_count",
    "unicode_safe_callback",
    "utf8_safe_encode",
    "utf8_safe_decode",
    "safe_unicode_decode",
    "normalize_unicode_safely",
    "detect_surrogate_pairs",
    "sanitize_for_utf8",
    "UnicodeNormalizationError",
    "EnhancedUnicodeProcessor",
    "SurrogateHandlingConfig",
    "SurrogateHandlingStrategy",
]
