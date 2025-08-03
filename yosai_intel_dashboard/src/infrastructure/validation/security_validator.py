from __future__ import annotations

import html
import os
import re
from typing import Iterable

try:  # pragma: no cover - allow using the validator without full core package
    from yosai_intel_dashboard.src.core.exceptions import ValidationError
except Exception:  # pragma: no cover
    class ValidationError(Exception):
        """Fallback validation error when core package is unavailable."""

# Import dynamically inside methods to avoid circular imports during module init

from .core import ValidationResult
from .file_validator import FileValidator
from .rules import CompositeValidator, ValidationRule


class XSSRule(ValidationRule):
    """Reject common cross-site scripting payloads."""

    PATTERN = re.compile(r"(<script|onerror=|javascript:)", re.IGNORECASE)

    def validate(self, data: str) -> ValidationResult:
        if self.PATTERN.search(data):
            return ValidationResult(False, data, ["xss"])
        return ValidationResult(True, html.escape(data))


class SQLRule(ValidationRule):
    """Detect basic SQL injection patterns."""

    PATTERN = re.compile(r"drop\s+table|delete\s+from|--", re.IGNORECASE)

    def validate(self, data: str) -> ValidationResult:
        if ";" in data and self.PATTERN.search(data):
            return ValidationResult(False, data, ["sql_injection"])
        return ValidationResult(True, data)


class InsecureDeserializationRule(ValidationRule):
    """Identify inputs that attempt unsafe object deserialization."""

    PATTERN = re.compile(r"(pickle\.loads|yaml\.load|!!python/object)", re.IGNORECASE)

    def validate(self, data: str) -> ValidationResult:
        if self.PATTERN.search(data):
            return ValidationResult(False, data, ["insecure_deserialization"])
        return ValidationResult(True, data)


class SSRFRule(ValidationRule):
    """Block URLs targeting internal services or local files."""

    LOCAL_PATTERN = re.compile(
        r"(?i)^(?:https?|ftp)://"
        r"(?:localhost|127\.0\.0\.1|169\.254\.169\.254|0\.0\.0\.0|"
        r"10\.|172\.(?:1[6-9]|2\d|3[0-1])|192\.168\.)"
    )
    SCHEME_PATTERN = re.compile(r"(?i)^(?:file|gopher|dict|smb)://")

    def validate(self, data: str) -> ValidationResult:
        if self.LOCAL_PATTERN.search(data) or self.SCHEME_PATTERN.search(data):
            return ValidationResult(False, data, ["ssrf"])
        return ValidationResult(True, data)


class SecurityValidator(CompositeValidator):
    """Validate input strings and file uploads against common OWASP risks.

    The validator combines multiple rules:
    - ``XSSRule`` for cross-site scripting.
    - ``SQLRule`` for SQL injection.
    - ``InsecureDeserializationRule`` for unsafe object deserialization.
    - ``SSRFRule`` for server-side request forgery.
    """

    def __init__(self, rules: Iterable[ValidationRule] | None = None) -> None:
        base_rules = list(
            rules
            or [
                XSSRule(),
                SQLRule(),
                InsecureDeserializationRule(),
                SSRFRule(),
            ]
        )
        super().__init__(base_rules)
        self.file_validator = FileValidator()

    def sanitize_filename(self, filename: str) -> str:
        """Return a safe filename stripped of path components."""
        name = os.path.basename(filename)
        if not name or name in {".", ".."}:
            raise ValidationError("Invalid filename")
        return name

    def validate_file_meta(self, filename: str, size_bytes: int) -> dict:
        """Validate filename and size limits without reading contents."""
        issues: list[str] = []
        try:
            sanitized = self.sanitize_filename(filename)
        except ValidationError:
            issues.append("Invalid filename")
            sanitized = os.path.basename(filename)

        # Import here to avoid circular dependencies during initialization
        from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
            dynamic_config,
        )

        max_bytes = dynamic_config.security.max_upload_mb * 1024 * 1024
        if size_bytes > max_bytes:
            issues.append("File too large")

        return {"valid": not issues, "issues": issues, "filename": sanitized}

    def validate_input(self, value: str, field_name: str = "input") -> dict:
        result = self.validate(value)
        if not result.valid:
            raise ValidationError("; ".join(result.issues or []))
        return {"valid": True, "sanitized": result.sanitized or value}

    def validate_file_upload(self, filename: str, content: bytes) -> dict:
        result = self.file_validator.validate_file_upload(filename, content)
        if not result["valid"]:
            raise ValidationError("; ".join(result["issues"]))
        return result


__all__ = [
    "SecurityValidator",
    "XSSRule",
    "SQLRule",
    "InsecureDeserializationRule",
    "SSRFRule",
    "FileValidator",
]
