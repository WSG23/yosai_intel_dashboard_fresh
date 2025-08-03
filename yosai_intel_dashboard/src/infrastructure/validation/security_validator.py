from __future__ import annotations

"""Security validation utilities.

This module exposes :class:`SecurityValidator` which can optionally incorporate
an anomaly detection model such as scikit-learn's ``IsolationForest``. The model
must implement a ``predict`` method returning ``1`` for normal inputs and ``-1``
for anomalies.

Example
-------
>>> from sklearn.ensemble import IsolationForest
>>> from validation.security_validator import SecurityValidator
>>> model = IsolationForest().fit([[1], [2], [3]])
>>> validator = SecurityValidator(anomaly_model=model)
>>> validator.validate_input("hello")  # doctest: +SKIP
{"valid": True, "sanitized": "hello"}
"""

import html
import logging
import os
import re
from functools import lru_cache

from typing import Iterable, Callable, Any
import logging


try:  # pragma: no cover - allow using the validator without full core package
    from yosai_intel_dashboard.src.core.exceptions import (
        ValidationError,
        TemporaryBlockError,
        PermanentBanError,
    )
except Exception:  # pragma: no cover
    class ValidationError(Exception):
        """Fallback validation error when core package is unavailable."""

    class TemporaryBlockError(Exception):
        pass

    class PermanentBanError(Exception):
        pass

try:  # pragma: no cover
    from yosai_intel_dashboard.src.infrastructure.cache import redis_client
except Exception:  # pragma: no cover
    redis_client = None

rate_limit = None
window_seconds = None


# Import dynamically inside methods to avoid circular imports during module init


from .core import ValidationResult
from .file_validator import FileValidator
from .rules import CompositeValidator, ValidationRule

# Import dynamically inside methods to avoid circular imports during module init


def _regex_validator(
    pattern: re.Pattern[str], issue: str
) -> Callable[[str], ValidationResult]:
    def _validate(data: str) -> ValidationResult:
        if pattern.search(data):
            return ValidationResult(False, data, [issue])
        return ValidationResult(True, data)

    return _validate


def _json_validator(data: str) -> ValidationResult:
    try:
        parsed = json.loads(data)
    except Exception:
        return ValidationResult(False, data, ["json"])
    return ValidationResult(True, json.dumps(parsed, ensure_ascii=False))


logger = logging.getLogger(__name__)


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


class IDORRule(ValidationRule):
    """Verify a user is authorized to access a given resource ID."""

    def __init__(self, user: Any, authorizer: Callable[[Any, str], bool]) -> None:
        self.user = user
        self.authorizer = authorizer

    def validate(self, data: str) -> ValidationResult:
        if not self.authorizer(self.user, data):
            return ValidationResult(False, data, ["unauthorized"])
        return ValidationResult(True, data)


class SecurityValidator(CompositeValidator):
    """Validate input strings and file uploads against common OWASP risks.

    The validator combines multiple rules:
    - ``XSSRule`` for cross-site scripting.
    - ``SQLRule`` for SQL injection.
    - ``InsecureDeserializationRule`` for unsafe object deserialization.
    - ``SSRFRule`` for server-side request forgery.
    """

    def __init__(
        self,
        rules: Iterable[ValidationRule] | None = None,
        authorize_resource: Callable[[Any, Any], bool] | None = None,
    ) -> None:
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
        self.redis = redis_client
        self.rate_limit = rate_limit or 0
        self.window_seconds = window_seconds or 0
        self.logger = logging.getLogger(__name__)
        self._authorize_resource = authorize_resource or (lambda _u, _r: True)

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


    @lru_cache(maxsize=128)
    def _cached_validate(self, value: str) -> ValidationResult:
        return super().validate(value)

    def sanitize_filename(self, filename: str) -> str:
        """Return a safe filename stripped of path components."""
        name = os.path.basename(filename)
        if name != filename or not name or name in {".", ".."}:
            raise ValidationError("Invalid filename")
        return name

    def validate_resource_id(self, user: Any, resource_id: Any) -> Any:
        """Validate that ``user`` is authorized for ``resource_id``."""
        rule = IDORRule(user, self._authorize_resource)
        result = rule.validate(str(resource_id))
        if not result.valid:
            raise ValidationError("Unauthorized resource access")
        return result.sanitized

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
    "InsecureDeserializationRule",
    "SSRFRule",
    "FileValidator",
]
