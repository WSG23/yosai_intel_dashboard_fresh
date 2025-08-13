class YosaiError(Exception):
    """Base exception for Yosai Intel Dashboard."""


class FileProcessingError(YosaiError):
    """Raised when file processing fails."""


class AuthError(YosaiError):
    """Raised for authentication related errors."""


class ExternalServiceError(YosaiError):
    """Raised when external service calls fail."""
