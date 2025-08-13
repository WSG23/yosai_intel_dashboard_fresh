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
import json
import logging
import mimetypes
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable

try:  # pragma: no cover - allow using the validator without full core package
    from yosai_intel_dashboard.src.core.exceptions import (
        PermanentBanError,
        TemporaryBlockError,
        ValidationError,
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

# Remediation suggestions for common validation issues
SUGGESTION_MAP: dict[str, str] = {
    "xss": "Remove script tags or encode the input.",
    "sql_injection": "Use parameterized queries instead of string concatenation.",
    "insecure_deserialization": "Avoid unsafe deserialization functions.",
    "ssrf": "Disallow requests to internal or file-based URLs.",
    "invalid_filename": "Provide a filename without path components.",
    "file_too_large": "Reduce the file size or increase the allowed limit.",
    "file_signature_mismatch": "Ensure the file extension matches its content.",
    "virus_detected": "Remove malware from the file before uploading.",
    "secret": "Remove secrets or credentials from the input.",
    "invalid_resource_id": "Use only letters, numbers, hyphens or underscores.",
    "anomaly": "Verify the input source or pattern.",
}

SECRET_PATTERN = re.compile(
    r"(AKIA[0-9A-Z]{16}|password=|secret|token=)", re.IGNORECASE
)
RESOURCE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


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
        *,
        secret_scan_hook: Callable[[ValidationResult], None] | None = None,
        anomaly_hook: Callable[[str, ValidationResult], None] | None = None,
        redis_client: Any | None = None,
        rate_limit: int | None = None,
        window_seconds: int | None = None,
        authorize_resource: Callable[[Any, str], bool] | None = None,
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
        self.secret_scan_hook = secret_scan_hook
        self.anomaly_hook = anomaly_hook
        self.redis = redis_client
        rl = rate_limit
        ws = window_seconds
        if rl is None or ws is None:
            from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
                dynamic_config,
            )

            rl = rl or dynamic_config.security.rate_limit_requests
            ws = ws or dynamic_config.security.rate_limit_window_minutes * 60
        self.rate_limit = rl
        self.window_seconds = ws

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

    def _augment(self, result: ValidationResult) -> ValidationResult:
        if result.issues:
            result.remediation = [
                SUGGESTION_MAP.get(issue, "") for issue in result.issues
            ]
            result.remediation = [r for r in result.remediation if r]
        return result

    def handle_secret_scan(self, result: ValidationResult) -> None:
        if self.secret_scan_hook:
            self.secret_scan_hook(result)

    def notify_anomaly(self, value: str, result: ValidationResult) -> None:
        if self.anomaly_hook:
            self.anomaly_hook(value, result)

    def sanitize_filename(self, filename: str) -> ValidationResult:
        """Return a safe filename stripped of path components."""
        name = Path(filename).name
        if name != filename or not name or name in {".", ".."}:
            return self._augment(ValidationResult(False, name, ["invalid_filename"]))
        return self._augment(ValidationResult(True, name))

    def validate_resource_access(self, user: Any, resource_id: Any) -> Any:
        """Ensure ``user`` is authorized to access ``resource_id``."""
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
        try:  # pragma: no cover - optional dependency
            import clamd
        except Exception as exc:  # pragma: no cover
            logger.debug("clamd not available: %s", exc)
            return None

        try:  # pragma: no cover - network interaction
            scanner = clamd.ClamdNetworkSocket()
            result = scanner.instream(io.BytesIO(content))
        except Exception as exc:  # pragma: no cover
            logger.warning("Virus scan failed: %s", exc)
            return None

        status, signature = result.get("stream", ("OK", None))
        if status == "FOUND":
            raise ValidationError(f"Virus detected: {signature}")

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

    def validate_file_meta(self, filename: str, content: bytes) -> ValidationResult:
        """Validate filename, size limits and basic file signatures."""
        issues: list[str] = []
        size_bytes = len(content)
        name_res = self.sanitize_filename(filename)
        sanitized = name_res.sanitized or Path(filename).name
        if not name_res.valid and name_res.issues:
            issues.extend(name_res.issues)

        # Import here to avoid circular dependencies during initialization
        from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
            dynamic_config,
        )

        max_bytes = dynamic_config.security.max_upload_mb * 1024 * 1024
        if size_bytes > max_bytes:
            issues.append("file_too_large")

        try:
            self._check_magic(filename, content)
        except ValidationError:
            issues.append("file_signature_mismatch")

        try:
            self._virus_scan(content)
        except ValidationError:
            issues.append("virus_detected")

        result = ValidationResult(
            not issues,
            {"filename": sanitized, "size_bytes": size_bytes},
            issues or None,
        )
        result = self._augment(result)
        if "secret" in (result.issues or []):
            self.handle_secret_scan(result)
        if not result.valid:
            self.notify_anomaly(filename, result)

        return result

    def validate_input(self, value: str, field_name: str = "input") -> ValidationResult:
        result = self._cached_validate(value)
        if SECRET_PATTERN.search(value):
            issues = (result.issues or []) + ["secret"]
            result = ValidationResult(False, value, issues)
            self.handle_secret_scan(result)
        result = self._augment(result)
        if not result.valid:
            logger.warning(
                "Validation failed for %s: %s",
                field_name,
                "; ".join(result.issues or []),
            )
            self.notify_anomaly(value, result)
        else:
            logger.info("Validation succeeded for %s", field_name)
        return result

    def scan_query(self, query: str) -> ValidationResult:
        """Scan a query string for insecure patterns and secrets."""
        result = self._cached_validate(query)
        if SECRET_PATTERN.search(query):
            issues = (result.issues or []) + ["secret"]
            result = ValidationResult(False, query, issues)
            self.handle_secret_scan(result)
        result = self._augment(result)
        if not result.valid:
            self.notify_anomaly(query, result)
        return result

    def validate_resource_id(self, resource_id: str) -> ValidationResult:
        """Validate identifiers for resources like files or database rows."""
        if RESOURCE_ID_PATTERN.fullmatch(resource_id):
            result = ValidationResult(True, resource_id)
        else:
            result = ValidationResult(False, resource_id, ["invalid_resource_id"])
        result = self._augment(result)
        if not result.valid:
            self.notify_anomaly(resource_id, result)
        return result

    def validate_file_upload(self, filename: str, content: bytes) -> ValidationResult:
        result_dict = self.file_validator.validate_file_upload(filename, content)
        if not result_dict["valid"]:

            logger.warning(
                "File '%s' failed validation: %s",
                filename,
                "; ".join(result_dict["issues"]),
            )
            result = ValidationResult(
                False, {"filename": filename}, result_dict["issues"]
            )
            self.notify_anomaly(filename, result)
            return self._augment(result)
        logger.info("File '%s' passed validation", filename)
        result = ValidationResult(
            True,
            {"filename": filename, "size_mb": result_dict["size_mb"]},
        )
        return self._augment(result)


__all__ = [
    "SecurityValidator",
    "XSSRule",
    "SQLRule",
    "InsecureDeserializationRule",
    "SSRFRule",
    "FileValidator",
]
