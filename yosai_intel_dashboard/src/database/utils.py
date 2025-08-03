"""Utility helpers for database connection strings.

Provides simple parsing and validation for PostgreSQL and SQLite
connection URLs used throughout the project.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass
class ParsedConnection:
    """Normalized representation of a database connection string."""

    dialect: str
    user: Optional[str] = None
    password: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    path: Optional[str] = None

    def build_url(self, override_dialect: Optional[str] = None) -> str:
        """Reconstruct a connection URL.

        Parameters
        ----------
        override_dialect:
            Optional scheme to use instead of the stored ``dialect``.
        """
        dialect = (override_dialect or self.dialect).lower()
        if dialect.startswith("sqlite"):
            path = self.path or ""
            if path.startswith("/"):
                return f"sqlite://{path}"
            return f"sqlite:///{path}"

        if dialect.startswith("postgres"):
            auth = ""
            if self.user:
                auth += self.user
                if self.password:
                    auth += f":{self.password}"
                auth += "@"
            host = self.host or ""
            port = f":{self.port}" if self.port else ""
            db = self.database or ""
            return f"{dialect}://{auth}{host}{port}/{db}"

        raise ValueError(f"Unsupported dialect: {dialect}")


def parse_connection_string(url: str) -> ParsedConnection:
    """Parse and validate *url* returning a :class:`ParsedConnection`.

    Supports ``postgresql`` and ``sqlite`` style URLs.  Raises ``ValueError``
    for unsupported schemes or missing required components.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    if scheme in {"postgresql", "postgres"}:
        if not parsed.path or parsed.path == "/":
            raise ValueError("PostgreSQL connection string must include database name")
        return ParsedConnection(
            dialect="postgresql",
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname or "",
            port=parsed.port or 5432,
            database=parsed.path.lstrip("/"),
        )

    if scheme == "sqlite":
        # sqlite:///tmp/db.sqlite -> path="/tmp/db.sqlite"
        path = parsed.path
        if parsed.netloc:
            # Handles strings like sqlite://localhost/tmp/db.sqlite
            path = f"/{parsed.netloc}{parsed.path}"
        if not path:
            raise ValueError("SQLite connection string must include database path")
        return ParsedConnection(dialect="sqlite", path=path)

    raise ValueError(f"Unsupported database scheme: {parsed.scheme}")


__all__ = ["ParsedConnection", "parse_connection_string"]
