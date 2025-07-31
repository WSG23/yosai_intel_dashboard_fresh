"""Custom exceptions for the application"""

from typing import Any, Dict, Optional

from shared.errors.types import ErrorCode


class YosaiBaseException(Exception):
    """Base exception for all Yōsai application errors"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: ErrorCode = ErrorCode.INTERNAL,
    ) -> None:
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class ConfigurationError(YosaiBaseException):
    """Configuration-related errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, ErrorCode.INTERNAL)


class DatabaseError(YosaiBaseException):
    """Database operation errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, ErrorCode.INTERNAL)


class ValidationError(YosaiBaseException):
    """Data validation errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, ErrorCode.INVALID_INPUT)


class SecurityError(YosaiBaseException):
    """Security-related errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, ErrorCode.UNAUTHORIZED)


class ServiceUnavailableError(YosaiBaseException):
    """Service unavailable errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details, ErrorCode.UNAVAILABLE)
