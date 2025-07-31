"""Database-related exception classes used across the code base."""

from __future__ import annotations


class DatabaseError(Exception):
    """Generic database operation error."""


class ConnectionRetryExhausted(DatabaseError):
    """Raised when a connection retry strategy gives up."""


class ConnectionValidationFailed(DatabaseError):
    """Raised when a connection health check fails."""


class UnicodeEncodingError(DatabaseError):
    """Raised when invalid Unicode is detected during SQL encoding."""

    def __init__(self, message: str, original_value: str) -> None:
        super().__init__(message)
        self.original_value = original_value


__all__ = [
    "DatabaseError",
    "ConnectionRetryExhausted",
    "ConnectionValidationFailed",
    "UnicodeEncodingError",
]
