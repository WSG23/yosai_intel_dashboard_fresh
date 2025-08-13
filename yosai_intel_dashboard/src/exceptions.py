from __future__ import annotations

class YosaiError(Exception):
    """Base exception for Yosai Intel Dashboard."""

class ExternalServiceError(YosaiError):
    """Raised when calls to external services fail."""

class InvalidResponseError(YosaiError):
    """Raised when external services return an unexpected response."""


class DownloadError(ExternalServiceError):
    """Raised when artifact downloads fail."""


class ConfigurationError(YosaiError):
    """Raised for configuration related errors."""
