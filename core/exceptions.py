"""Custom exceptions for the application"""

from typing import Optional, Dict, Any


class YosaiBaseException(Exception):
    """Base exception for all Yōsai application errors"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class ConfigurationError(YosaiBaseException):
    """Configuration-related errors"""


class DatabaseError(YosaiBaseException):
    """Database operation errors"""


class ValidationError(YosaiBaseException):
    """Data validation errors"""


class SecurityError(YosaiBaseException):
    """Security-related errors"""


class FileProcessingError(YosaiBaseException):
    """File processing errors"""


class ServiceUnavailableError(YosaiBaseException):
    """Service unavailable errors"""
