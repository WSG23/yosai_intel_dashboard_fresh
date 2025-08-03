from __future__ import annotations

import html
import logging
import os
import re
from typing import Any, Iterable

from yosai_intel_dashboard.src.core.exceptions import (
    PermanentBanError,
    TemporaryBlockError,
    ValidationError,
)
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

    def __init__(
        self,
        rules: Iterable[ValidationRule] | None = None,
        redis_client: Any | None = None,
        rate_limit: int | None = None,
        window_seconds: int | None = None,
    ) -> None:
        base_rules = list(rules or [XSSRule(), SQLRule()])
        super().__init__(base_rules)
        self.file_validator = FileValidator()
        self.redis = redis_client
        if rate_limit is None or window_seconds is None:
            from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
                dynamic_config,
            )

            rate_limit = rate_limit or dynamic_config.security.rate_limit_requests
            window_seconds = (
                window_seconds
                or dynamic_config.security.rate_limit_window_minutes * 60
            )
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.logger = logging.getLogger(__name__)

    def _check_rate_limit(self, identifier: str) -> None:
        if not self.redis:
            return
        key = f"rl:{identifier}"
        count = self.redis.incr(key)
        if count == 1:
            self.redis.expire(key, self.window_seconds)
        if count <= self.rate_limit:
            return
        esc_key = f"rl:esc:{identifier}"
        level = self.redis.incr(esc_key)
        if level == 1:
            self.logger.warning("Rate limit exceeded for %s", identifier)
        elif level == 2:
            self.logger.warning("Temporary block for %s", identifier)
            raise TemporaryBlockError("Rate limit exceeded")
        else:
            self.logger.error("Permanent ban for %s", identifier)
            raise PermanentBanError("Rate limit exceeded")

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

    def validate_input(
        self, value: str, field_name: str = "input", identifier: str | None = None
    ) -> dict:
        self._check_rate_limit(identifier or "global")
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
