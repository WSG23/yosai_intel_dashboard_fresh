from __future__ import annotations

"""Helpers for SQL-safe Unicode encoding."""

from typing import Any, Optional

from .core import UnicodeProcessor


def encode_query(query: Any, processor: Optional[UnicodeProcessor] = None) -> str:
    """Return ``query`` cleaned for safe SQL execution."""

    if processor is None:
        processor = UnicodeProcessor()

    cleaned = processor.process(query)
    try:
        cleaned.encode("utf-8")
    except Exception:
        cleaned = cleaned.encode("utf-8", "ignore").decode("utf-8", "ignore")
    return cleaned


__all__ = ["encode_query"]
