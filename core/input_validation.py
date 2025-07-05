from __future__ import annotations

"""Unified input validation utilities combining simple and comprehensive checks.

This module now consolidates the previous ``services.input_validator`` helper
so that both string sanitisation and basic file upload validation live in a
single place.  ``InputValidator`` therefore exposes lightweight file
validation via :meth:`validate_file_upload` alongside wrappers around the more
comprehensive :class:`core.security.InputValidator`.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Dict, Optional

import bleach

from core.unicode_processor import sanitize_unicode_input
from security.validation_exceptions import ValidationError
from core.security import InputValidator as _ComprehensiveValidator
from config.dynamic_config import dynamic_config


class Validator(Protocol):
    """Validator protocol for simple validators."""

    def validate(self, data: Any) -> Any: ...


@dataclass
class ValidationResult:
    """Result of validating an uploaded file."""

    valid: bool
    message: str = ""


class InputValidator:
    """Wrapper combining legacy InputValidator behaviour with the comprehensive
    :class:`core.security.InputValidator` implementation."""

    _dangerous_pattern = re.compile(
        r"(<script.*?>.*?</script>|<.*?on\w+\s*=|javascript:|data:text/html|[<>])",
        re.IGNORECASE | re.DOTALL,
    )

    def __init__(self, max_size_mb: Optional[int] = None) -> None:
        self._validator = _ComprehensiveValidator()
        self.max_size_mb = max_size_mb or dynamic_config.security.max_upload_mb

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

    def validate_secure_upload(
        self, filename: str, file_content: bytes, max_size_mb: int | None = None
    ) -> Dict[str, Any]:
        """Delegate to the comprehensive validator for strict checks."""
        if max_size_mb is None:
            return self._validator.validate_file_upload(filename, file_content)
        return self._validator.validate_file_upload(filename, file_content, max_size_mb)

    def validate_file_upload(self, file_obj: Any) -> ValidationResult:
        """Validate an uploaded file-like object using lightweight checks."""
        if file_obj is None:
            return ValidationResult(False, "No file provided")

        try:
            import pandas as pd

            if isinstance(file_obj, pd.DataFrame):
                if file_obj.empty:
                    return ValidationResult(False, "Empty dataframe")
                size_mb = file_obj.memory_usage(deep=True).sum() / (1024 * 1024)
                if size_mb > self.max_size_mb:
                    return ValidationResult(
                        False,
                        f"Dataframe too large: {size_mb:.1f}MB > {self.max_size_mb}MB",
                    )
                return ValidationResult(True, "ok")
        except Exception:
            pass

        if isinstance(file_obj, (str, Path)):
            path = Path(file_obj)
            if not path.exists():
                return ValidationResult(False, "File not found")
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb == 0:
                return ValidationResult(False, "File is empty")
            if size_mb > self.max_size_mb:
                return ValidationResult(
                    False,
                    f"File too large: {size_mb:.1f}MB > {self.max_size_mb}MB",
                )
            return ValidationResult(True, "ok")

        if isinstance(file_obj, (bytes, bytearray)):
            size_mb = len(file_obj) / (1024 * 1024)
            if size_mb == 0:
                return ValidationResult(False, "File is empty")
            if size_mb > self.max_size_mb:
                return ValidationResult(
                    False,
                    f"File too large: {size_mb:.1f}MB > {self.max_size_mb}MB",
                )
            return ValidationResult(True, "ok")

        return ValidationResult(False, "Unsupported file type")


# Module level instance and helper functions
input_validator = InputValidator()


def validate_input(input_data: str, field_name: str = "input") -> Dict[str, Any]:
    """Convenience wrapper using the module level :data:`input_validator`."""
    return input_validator.validate_input(input_data, field_name)


def validate_file_upload(
    filename: str, file_content: bytes, max_size_mb: int | None = None
) -> Dict[str, Any]:
    """Backward compatible wrapper for strict file upload validation."""
    return input_validator.validate_secure_upload(filename, file_content, max_size_mb)


__all__ = [
    "InputValidator",
    "Validator",
    "ValidationResult",
    "validate_input",
    "validate_file_upload",
    "input_validator",
]
