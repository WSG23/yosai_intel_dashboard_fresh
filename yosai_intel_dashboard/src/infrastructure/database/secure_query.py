from __future__ import annotations

"""Utility helpers for building and logging parameterized SQL queries safely.

This module exposes :class:`SecureQueryBuilder` which includes helpers for
constructing queries with validated identifiers such as :meth:`build_select`.
"""

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Set, Tuple

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name: str, allowed: Set[str]) -> str:
    if name not in allowed or not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Unapproved identifier: {name}")
    return name


The SecureQueryBuilder implementation has moved to
``infrastructure.security.query_builder``. Importing from this module is
deprecated and will be removed in a future release.
"""

def log_sanitized_query(
    logger: logging.Logger, sql: str, params: Sequence[Any] | None
) -> None:
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

    def build_select(
        self,
        table: str,
        columns: Sequence[str],
        where: Mapping[str, Any] | None = None,
        *,
        timeout: int | None = None,
        logger: logging.Logger | None = None,
    ) -> Tuple[str, Sequence[Any] | None]:
        """Construct a parameterized ``SELECT`` statement.

        Parameters
        ----------
        table:
            Target table name which must be present in ``allowed_tables``.
        columns:
            Iterable of column names for the ``SELECT`` clause; every column
            must be in ``allowed_columns``.
        where:
            Optional mapping of column names to values used to build an
            equality-based ``WHERE`` clause. Keys are validated against
            ``allowed_columns`` and values become parameters.
        timeout:
            Optional per-query timeout overriding ``default_timeout``.
        logger:
            Optional logger for sanitized SQL output.

        Returns
        -------
        Tuple[str, Sequence[Any] | None]
            The SQL string and parameters tuple.

        Raises
        ------
        ValueError
            If any table or column name is not allow-listed.
        """

        table_q = self.table(table)
        column_qs = ", ".join(self.column(c) for c in columns)
        sql = f"SELECT {column_qs} FROM {table_q}"
        params: list[Any] = []
        if where:
            clauses = []
            for i, (col, value) in enumerate(where.items(), start=1):
                col_q = self.column(col)
                clauses.append(f"{col_q} = ${i}")
                params.append(value)
            sql += " WHERE " + " AND ".join(clauses)
        return self.build(
            sql, tuple(params) if params else None, timeout=timeout, logger=logger
        )

    def build(
        self,
        sql: str,
        *tables_or_params: Any,
        timeout: int | None = None,
        logger: logging.Logger | None = None,
    ) -> Tuple[str, Sequence[Any] | None]:
        params: Sequence[Any] | None = None
        tables: Tuple[str, ...] = ()
        if tables_or_params:
            last = tables_or_params[-1]
            if isinstance(last, Sequence) and not isinstance(last, (str, bytes)):
                params = last
                tables = tuple(tables_or_params[:-1])
            else:
                tables = tuple(tables_or_params)
        if tables:
            validated = tuple(
                _validate_identifier(t, self.allowed_tables) for t in tables
            )
            sql = sql % validated
        tokens = sql.split()
        if len(tokens) > self.max_tokens:
            raise ValueError("Query exceeds complexity limits")
        if logger:
            log_sanitized_query(logger, sql, params)
        self.default_timeout = timeout or self.default_timeout
        return sql, params



__all__ = ["SecureQueryBuilder", "log_sanitized_query"]
