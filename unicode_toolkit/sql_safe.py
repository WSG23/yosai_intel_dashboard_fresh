from __future__ import annotations

"""Helpers for SQL-safe Unicode encoding."""

from typing import Any, Optional

from yosai_intel_dashboard.src.core.unicode import UnicodeSQLProcessor


def encode_query(query: Any, processor: Optional[object] = None) -> str:
    """Return ``query`` cleaned for safe SQL execution."""

    # ``processor`` argument kept for backward compatibility
    return UnicodeSQLProcessor.encode_query(query)


__all__ = ["encode_query"]
