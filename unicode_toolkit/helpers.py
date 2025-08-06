"""Helper utilities built on top of :mod:`unicode_toolkit` core."""

from __future__ import annotations

from base64 import b64decode
from typing import Any, Iterable, Optional, Tuple

from yosai_intel_dashboard.src.core.unicode import (
    UnicodeSQLProcessor,
)
from yosai_intel_dashboard.src.core.unicode import clean_unicode_surrogates as _clean_unicode_surrogates
from yosai_intel_dashboard.src.core.base_utils import safe_encode_text as _safe_encode_text
from yosai_intel_dashboard.src.core.unicode import (
    sanitize_dataframe,
)


def clean_unicode_text(text: Any) -> str:
    """Normalize and strip dangerous characters from ``text``."""
    return _safe_encode_text(text)


def clean_unicode_surrogates(text: Any) -> str:
    """Return ``text`` with UTF-16 surrogate code points removed."""
    return _clean_unicode_surrogates(str(text))


def safe_encode_text(value: Any) -> str:
    """Public wrapper mirroring legacy ``safe_encode_text``."""
    return _safe_encode_text(value)


class UnicodeQueryHandler:
    """Encode SQL queries and parameters using :class:`UnicodeProcessor`."""

    @staticmethod
    def safe_encode_query(query: Any) -> str:
        return UnicodeSQLProcessor.encode_query(query)

    @staticmethod
    def safe_encode_params(params: Optional[Iterable[Any]]) -> Optional[Iterable[Any]]:
        if params is None:
            return None
        encoded = []
        for item in params:
            if isinstance(item, str):
                encoded.append(UnicodeSQLProcessor.encode_query(item))
            else:
                encoded.append(item)
        return type(params)(encoded)


def decode_upload_content(content: str, filename: str) -> Tuple[bytes, str]:
    """Decode upload ``content`` from base64 and return bytes and file extension."""
    try:
        data = b64decode(content)
    except Exception:
        data = b""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return data, ext


__all__ = [
    "clean_unicode_surrogates",
    "clean_unicode_text",
    "safe_encode_text",
    "UnicodeQueryHandler",
    "decode_upload_content",
    "sanitize_dataframe",
]
