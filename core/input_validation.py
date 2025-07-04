from __future__ import annotations

"""Unified input validation utilities combining simple and comprehensive checks."""

import re
from typing import Any, Protocol, Dict

import bleach

from core.unicode_utils import sanitize_unicode_input
from security.validation_exceptions import ValidationError
from core.security import InputValidator as _ComprehensiveValidator


class Validator(Protocol):
    """Validator protocol for simple validators."""

    def validate(self, data: Any) -> Any: ...


class InputValidator:
    """Wrapper combining legacy InputValidator behaviour with the comprehensive
    :class:`core.security.InputValidator` implementation."""

    _dangerous_pattern = re.compile(
        r"(<script.*?>.*?</script>|<.*?on\w+\s*=|javascript:|data:text/html|[<>])",
        re.IGNORECASE | re.DOTALL,
    )

    def __init__(self) -> None:
        self._validator = _ComprehensiveValidator()

    def validate(self, data: str) -> str:
        """Validate and sanitize a string.

        This maintains the old ``InputValidator`` interface which returned the
        sanitized string or raised :class:`ValidationError` on failure.
        """
        cleaned = sanitize_unicode_input(str(data))
        if self._dangerous_pattern.search(cleaned):
            raise ValidationError("Potentially dangerous characters detected")

        result = self._validator.validate_input(cleaned, "input")
        if not result["valid"]:
            raise ValidationError("; ".join(result["issues"]))

        return bleach.clean(result["sanitized"], strip=True)

    # Expose common methods from the comprehensive validator
    def validate_input(
        self, input_data: str, field_name: str = "input"
    ) -> Dict[str, Any]:
        return self._validator.validate_input(input_data, field_name)

    def validate_file_upload(
        self, filename: str, file_content: bytes, max_size_mb: int = None
    ) -> Dict[str, Any]:
        if max_size_mb is None:
            return self._validator.validate_file_upload(filename, file_content)
        return self._validator.validate_file_upload(filename, file_content, max_size_mb)


# Module level instance and helper functions
input_validator = InputValidator()


def validate_input(input_data: str, field_name: str = "input") -> Dict[str, Any]:
    """Convenience wrapper using the module level :data:`input_validator`."""
    return input_validator.validate_input(input_data, field_name)


def validate_file_upload(
    filename: str, file_content: bytes, max_size_mb: int | None = None
) -> Dict[str, Any]:
    """Convenience wrapper delegating to :data:`input_validator`."""
    if max_size_mb is None:
        return input_validator.validate_file_upload(filename, file_content)
    return input_validator.validate_file_upload(filename, file_content, max_size_mb)


__all__ = [
    "InputValidator",
    "Validator",
    "validate_input",
    "validate_file_upload",
    "input_validator",
]
