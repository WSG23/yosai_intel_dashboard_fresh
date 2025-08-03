from __future__ import annotations

"""Utility helpers for building and logging parameterized SQL queries safely."""

import logging
import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence, Tuple, Any, Set

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name: str, allowed: Set[str]) -> str:
    if name not in allowed or not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Unapproved identifier: {name}")
    return name


def log_sanitized_query(logger: logging.Logger, sql: str, params: Sequence[Any] | None) -> None:
    """Log *sql* with params redacted as placeholders."""
    if params:
        redacted = tuple("?" for _ in params)
        logger.debug("SQL: %s params=%s", sql, redacted)
    else:
        logger.debug("SQL: %s", sql)


@dataclass
class SecureQueryBuilder:
    """Minimal query builder enforcing identifier allow-lists and limits."""

    allowed_tables: Set[str] = field(default_factory=set)
    allowed_columns: Set[str] = field(default_factory=set)
    max_tokens: int = 500
    default_timeout: int | None = None

    def table(self, name: str) -> str:
        return _validate_identifier(name, self.allowed_tables)

    def column(self, name: str) -> str:
        return _validate_identifier(name, self.allowed_columns)

    def build(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
        *,
        timeout: int | None = None,
        logger: logging.Logger | None = None,
    ) -> Tuple[str, Sequence[Any] | None]:
        tokens = sql.split()
        if len(tokens) > self.max_tokens:
            raise ValueError("Query exceeds complexity limits")
        if logger:
            log_sanitized_query(logger, sql, params)
        self.default_timeout = timeout or self.default_timeout
        return sql, params

__all__ = ["SecureQueryBuilder", "log_sanitized_query"]
