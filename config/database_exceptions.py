class DatabaseError(Exception):
    """Base database error."""


class ConnectionRetryExhausted(DatabaseError):
    """Raised when connection retries are exhausted."""


class ConnectionValidationFailed(DatabaseError):
    """Raised when a connection health check fails."""


class UnicodeEncodingError(DatabaseError):
    """Raised when Unicode encoding fails."""

