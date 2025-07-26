"""Base validation protocol and default implementations."""

from __future__ import annotations

from typing import Any, Protocol

from validation.security_validator import SecurityValidator as _LegacySecurityValidator
from validation.unicode_validator import UnicodeValidator as _LegacyUnicodeValidator


class BaseValidator(Protocol):
    """Simple validator interface."""

    def validate(self, data: Any) -> Any:
        """Validate ``data`` and return the sanitized value."""


class SecurityValidator(BaseValidator):
    """Validate input for common security issues."""

    def __init__(self) -> None:
        self._validator = _LegacySecurityValidator()

    def validate(self, data: str) -> str:
        result = self._validator.validate_input(str(data), "input")
        return result["sanitized"]


class UnicodeValidator(BaseValidator):
    """Validate and sanitize unicode text."""

    def __init__(self) -> None:
        self._validator = _LegacyUnicodeValidator()

    def validate(self, data: Any) -> str:
        return self._validator.validate_text(data)


class BusinessValidator(BaseValidator):
    """Apply unicode and security validation in sequence."""

    def __init__(self) -> None:
        self._unicode = UnicodeValidator()
        self._security = SecurityValidator()

    def validate(self, data: Any) -> str:
        sanitized = self._unicode.validate(data)
        return self._security.validate(sanitized)


__all__ = [
    "BaseValidator",
    "SecurityValidator",
    "UnicodeValidator",
    "BusinessValidator",
]
