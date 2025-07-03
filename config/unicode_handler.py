from __future__ import annotations

from typing import Any

from .database_exceptions import UnicodeEncodingError


class UnicodeQueryHandler:
    """Utility for safely encoding SQL queries and parameters."""

    @staticmethod
    def _encode(value: Any) -> Any:
        if isinstance(value, str):
            try:
                data = value.encode("utf-8", "surrogateescape")
                return data.decode("utf-8", "replace")
            except Exception as exc:
                raise UnicodeEncodingError(str(exc)) from exc
        if isinstance(value, dict):
            return {k: UnicodeQueryHandler._encode(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return type(value)(UnicodeQueryHandler._encode(v) for v in value)
        return value

    @classmethod
    def safe_encode_query(cls, query: str) -> str:
        return cls._encode(query)

    @classmethod
    def safe_encode_params(cls, params: Any) -> Any:
        return cls._encode(params)
