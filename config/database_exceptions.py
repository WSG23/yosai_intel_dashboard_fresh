"""Database-related exception classes."""

from yosai_intel_dashboard.src.infrastructure.config.database_exceptions import (
    DatabaseError,
    ConnectionRetryExhausted,
    ConnectionValidationFailed,
    UnicodeEncodingError,
)

__all__ = [
    "DatabaseError",
    "ConnectionRetryExhausted",
    "ConnectionValidationFailed",
    "UnicodeEncodingError",
]
