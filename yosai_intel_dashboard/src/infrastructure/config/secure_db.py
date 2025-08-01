"""Helpers for executing sanitized database queries."""

from __future__ import annotations

from typing import Any, Iterable, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from yosai_intel_dashboard.src.core.unicode import UnicodeSQLProcessor
from database.secure_exec import execute_secure_query as _exec_secure_query

__all__ = ["execute_secure_query"]


def execute_secure_query(
    conn: Any, query: str, params: Iterable[Any] | None = None
) -> Any:
    """Encode ``query`` and ``params`` safely then execute using ``conn``."""
    from yosai_intel_dashboard.src.core.unicode import UnicodeSQLProcessor

    sanitized_query = UnicodeSQLProcessor.encode_query(query)
    sanitized_params = None
    if params is not None:
        sanitized_params = tuple(
            UnicodeSQLProcessor.encode_query(p) if isinstance(p, str) else p
            for p in params
        )
    else:
        sanitized_params = ()
    return _exec_secure_query(conn, sanitized_query, sanitized_params)
