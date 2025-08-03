from __future__ import annotations

import html
import os
import re
from functools import lru_cache
from typing import Iterable
import logging

from yosai_intel_dashboard.src.core.exceptions import ValidationError
# Import dynamically inside methods to avoid circular imports during module init

from .core import ValidationResult
from .file_validator import FileValidator
from .rules import CompositeValidator, ValidationRule


logger = logging.getLogger(__name__)


class XSSRule(ValidationRule):
    PATTERN = re.compile(r"(<script|onerror=|javascript:)", re.IGNORECASE)

    def validate(self, data: str) -> ValidationResult:
        if self.PATTERN.search(data):
            return ValidationResult(False, data, ["xss"])
        return ValidationResult(True, html.escape(data))


class SQLRule(ValidationRule):
    PATTERN = re.compile(r"drop\s+table|delete\s+from|--", re.IGNORECASE)

    def validate(self, data: str) -> ValidationResult:
        if ";" in data and self.PATTERN.search(data):
            return ValidationResult(False, data, ["sql_injection"])
        return ValidationResult(True, data)


class SecurityValidator(CompositeValidator):
    """Validate input strings and file uploads."""

    def __init__(self, rules: Iterable[ValidationRule] | None = None) -> None:
        base_rules = list(rules or [XSSRule(), SQLRule()])
        super().__init__(base_rules)
        self.file_validator = FileValidator()

    @lru_cache(maxsize=128)
    def _cached_validate(self, value: str) -> ValidationResult:
        return super().validate(value)

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

        result = {"valid": not issues, "issues": issues, "filename": sanitized}
        if result["valid"]:
            logger.info("File metadata for '%s' is valid", filename)
        else:
            logger.warning(
                "File metadata validation failed for '%s': %s",
                filename,
                "; ".join(result["issues"]),
            )
        return result

    def validate_input(self, value: str, field_name: str = "input") -> dict:
        result = self._cached_validate(value)
        if not result.valid:
            logger.warning(
                "Validation failed for %s: %s",
                field_name,
                "; ".join(result.issues or []),
            )
            raise ValidationError("; ".join(result.issues or []))
        logger.info("Validation succeeded for %s", field_name)
        return {"valid": True, "sanitized": result.sanitized or value}

    def validate_file_upload(self, filename: str, content: bytes) -> dict:
        result = self.file_validator.validate_file_upload(filename, content)
        if not result["valid"]:
            logger.warning(
                "File '%s' failed validation: %s", filename, "; ".join(result["issues"])
            )
            raise ValidationError("; ".join(result["issues"]))
        logger.info("File '%s' passed validation", filename)
        return result


__all__ = [
    "SecurityValidator",
    "XSSRule",
    "SQLRule",
    "FileValidator",
]
