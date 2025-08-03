from __future__ import annotations

import html
import os
import re
from pathlib import Path
from typing import Iterable

from yosai_intel_dashboard.src.core.exceptions import ValidationError
# Import dynamically inside methods to avoid circular imports during module init

from .core import ValidationResult
from .file_validator import FileValidator
from .rules import CompositeValidator, ValidationRule


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

    def sanitize_filename(self, filename: str) -> str:
        """Return a safe filename stripped of path components."""
        name = os.path.basename(filename)
        if name != filename or not name or name in {".", ".."}:
            raise ValidationError("Invalid filename")
        return name

    # ------------------------------------------------------------------
    def _virus_scan(self, content: bytes) -> None:
        """Hook for virus scanning.

        Integrators can override this method to connect to an external
        scanner. The hook should raise :class:`ValidationError` if malicious
        content is detected.
        """

        return None

    def _check_magic(self, filename: str, content: bytes) -> None:
        """Validate that ``content`` matches the expected file signature."""

        magic_map: dict[str, bytes] = {
            ".png": b"\x89PNG\r\n\x1a\n",
            ".jpg": b"\xff\xd8\xff",
            ".jpeg": b"\xff\xd8\xff",
            ".pdf": b"%PDF-",
            ".gif": b"GIF8",
            ".xlsx": b"PK\x03\x04",
            ".xls": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
        }

        ext = Path(filename).suffix.lower()
        sig = magic_map.get(ext)
        header = content[:8]
        if sig and not header.startswith(sig):
            raise ValidationError("File signature mismatch")

        if not sig:
            for expected_ext, expected_sig in magic_map.items():
                if header.startswith(expected_sig):
                    raise ValidationError("File extension does not match content")

    def validate_file_meta(self, filename: str, content: bytes) -> dict:
        """Validate filename, size limits and basic file signatures."""
        issues: list[str] = []
        size_bytes = len(content)
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

        self._check_magic(sanitized, content)
        self._virus_scan(content)

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
    "FileValidator",
]
