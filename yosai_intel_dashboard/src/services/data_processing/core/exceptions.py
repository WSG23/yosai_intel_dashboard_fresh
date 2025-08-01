"""File processing exception hierarchy."""

from yosai_intel_dashboard.src.core.exceptions import YosaiBaseException
from shared.errors.types import ErrorCode


class FileProcessingError(YosaiBaseException):
    """Base exception for file processing errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, details, ErrorCode.INVALID_INPUT)


class FileValidationError(FileProcessingError):
    """Raised when validation of a file fails."""


class FileFormatError(FileProcessingError):
    """Raised for unsupported or corrupt file formats."""


class FileSizeError(FileProcessingError):
    """Raised when a file exceeds allowed size limits."""


class FileSecurityError(FileProcessingError):
    """Raised when a security issue is detected in a file."""


__all__ = [
    "FileProcessingError",
    "FileValidationError",
    "FileFormatError",
    "FileSizeError",
    "FileSecurityError",
]
