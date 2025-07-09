"""Database-related exception classes."""

from typing import Any, Optional


class DatabaseError(Exception):
    """Base exception for database operations."""

    pass


class ConnectionRetryExhausted(DatabaseError):
    """Exception raised when connection retry attempts are exhausted."""

    def __init__(self, message: str, retry_count: int = 0) -> None:
        super().__init__(message)
        self.retry_count = retry_count


class ConnectionValidationFailed(DatabaseError):
    """Exception raised when database connection validation fails."""

    pass


class UnicodeEncodingError(DatabaseError):
    """Exception raised when Unicode encoding fails in database operations."""

    def __init__(self, message: str, original_value: Optional[Any] = None) -> None:
        super().__init__(message)
        self.original_value = original_value


__all__ = [
    "DatabaseError",
    "ConnectionRetryExhausted",
    "ConnectionValidationFailed",
    "UnicodeEncodingError",
]
