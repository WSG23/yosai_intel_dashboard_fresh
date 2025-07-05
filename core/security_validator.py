"""
Enhanced Security Validation for Yōsai Intel Dashboard
Implements comprehensive input validation and security checks
"""

import logging
import re
import os
import secrets
from typing import Dict, Any, List, Callable

from config.constants import FileProcessingLimits

from core.unicode_processor import sanitize_unicode_input
from dataclasses import dataclass
from enum import Enum
from .security_patterns import (
    XSS_PATTERNS as RAW_XSS_PATTERNS,
    PATH_TRAVERSAL_PATTERNS as RAW_PATH_PATTERNS,
)
from security.sql_validator import SQLInjectionPrevention
from core.exceptions import ValidationError
from security_callback_controller import (
    emit_security_event,
    SecurityEvent,

)


class SecurityLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SecurityIssue:
    level: SecurityLevel
    message: str
    field: str
    recommendation: str


class SecurityValidator:
    """Comprehensive security validator"""

    VALIDATION_CONFIG = {
        "sql_injection": True,
        "xss": True,
        "path_traversal": True,
    }

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    # Compiled patterns for performance
    XSS_PATTERNS = [re.compile(p, re.IGNORECASE) for p in RAW_XSS_PATTERNS]

    PATH_PATTERNS = [re.compile(p, re.IGNORECASE) for p in RAW_PATH_PATTERNS]

    def validate_input(self, value: str, field_name: str = "input") -> Dict[str, Any]:
        """Orchestrate security validations for the given value."""
        sanitized = self._sanitize_input(value)
        issues: List[SecurityIssue] = []

        validators: List[Callable[[str, str], List[SecurityIssue]]] = []
        if self.VALIDATION_CONFIG.get("sql_injection"):
            validators.append(self._validate_sql_injection)
        if self.VALIDATION_CONFIG.get("xss"):
            validators.append(self._validate_xss_patterns)
        if self.VALIDATION_CONFIG.get("path_traversal"):
            validators.append(self._validate_path_traversal)

        for validator in validators:
            issues.extend(
                self._validate_with_error_handling(validator, sanitized, field_name)
            )
            if any(issue.level == SecurityLevel.CRITICAL for issue in issues):
                break

        return self._compile_validation_results(issues, sanitized)

    def _sanitize_input(self, value: str) -> str:
        """Sanitize input by encoding dangerous characters"""
        value = sanitize_unicode_input(value)
        # HTML entity encoding
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;",
        }

        sanitized = value
        for char, entity in replacements.items():
            sanitized = sanitized.replace(char, entity)

        return sanitized

    def _validate_sql_injection(
        self, value: str, field_name: str
    ) -> List[SecurityIssue]:
        """Check for SQL injection patterns."""
        validator = SQLInjectionPrevention()
        try:
            validator.validate_query_parameter(value)
            return []
        except ValidationError:
            return [
                self._create_security_issue(
                    SecurityLevel.CRITICAL,
                    "Potential SQL injection detected",
                    field_name,
                    "Use parameterized queries and input sanitization",
                )
            ]

    def _validate_xss_patterns(
        self, value: str, field_name: str
    ) -> List[SecurityIssue]:
        """Check for cross-site scripting patterns."""
        issues = []
        for pattern in self.XSS_PATTERNS:
            if pattern.search(value):
                issues.append(
                    self._create_security_issue(
                        SecurityLevel.HIGH,
                        "Potential XSS attack detected",
                        field_name,
                        "Encode output and validate input",
                    )
                )
                break
        return issues

    def _validate_path_traversal(
        self, value: str, field_name: str
    ) -> List[SecurityIssue]:
        """Check for path traversal attempts."""
        issues = []
        for pattern in self.PATH_PATTERNS:
            if pattern.search(value):
                issues.append(
                    self._create_security_issue(
                        SecurityLevel.HIGH,
                        "Potential path traversal detected",
                        field_name,
                        "Restrict file access and validate paths",
                    )
                )
                break
        return issues

    def _create_security_issue(
        self,
        level: SecurityLevel,
        message: str,
        field_name: str,
        recommendation: str,
    ) -> SecurityIssue:
        """Factory for SecurityIssue objects."""
        return SecurityIssue(
            level=level,
            message=message,
            field=field_name,
            recommendation=recommendation,
        )

    def _validate_with_error_handling(
        self,
        validator_func: Callable[[str, str], List[SecurityIssue]],
        value: str,
        field_name: str,
    ) -> List[SecurityIssue]:
        """Execute a validator and handle exceptions gracefully."""
        try:
            return validator_func(value, field_name)
        except Exception as exc:
            self.logger.error(
                "Validation error in %s: %s", validator_func.__name__, exc
            )
            return [
                self._create_security_issue(
                    SecurityLevel.MEDIUM,
                    f"Validation error: {exc}",
                    field_name,
                    "Review input validation system",
                )
            ]

    def _compile_validation_results(
        self, issues: List[SecurityIssue], sanitized_value: str
    ) -> Dict[str, Any]:
        """Compile the final validation result dictionary."""
        severity = max((issue.level for issue in issues), default=SecurityLevel.LOW)
        result = {
            "valid": len(issues) == 0,
            "issues": issues,
            "sanitized": sanitized_value,
            "severity": severity,
        }
        if not result["valid"]:
            emit_security_event(
                SecurityEvent.VALIDATION_FAILED,
                {"severity": severity.name, "issue_count": len(issues)},
            )
        return result

    def get_available_validators(self) -> List[str]:
        """Return the list of enabled validators."""
        return [name for name, enabled in self.VALIDATION_CONFIG.items() if enabled]

    def validate_single_pattern(
        self, pattern_type: str, value: str, field_name: str
    ) -> List[SecurityIssue]:
        """Run a single validator by pattern type."""
        mapping = {
            "sql_injection": self._validate_sql_injection,
            "xss": self._validate_xss_patterns,
            "path_traversal": self._validate_path_traversal,
        }
        validator = mapping.get(pattern_type)
        if not validator:
            raise ValueError(f"Unknown validator: {pattern_type}")
        return validator(value, field_name)

    @staticmethod
    def generate_secure_secret(length: int = 32) -> str:
        """Generate cryptographically secure secret key"""
        return secrets.token_hex(length)

    @staticmethod
    def validate_file_upload(
        filename: str,
        content: bytes,
        max_size_mb: int = FileProcessingLimits.MAX_FILE_UPLOAD_SIZE_MB,
    ) -> Dict[str, Any]:
        """Validate file uploads for security"""
        issues: List[str] = []

        # Check file size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > max_size_mb:
            issues.append(f"File too large: {size_mb:.1f}MB > {max_size_mb}MB")

        # Check filename
        if ".." in filename or "/" in filename or "\\" in filename:
            issues.append("Invalid filename: contains path traversal characters")

        # Check file extension
        allowed_extensions = {".csv", ".json", ".xlsx", ".xls"}
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            issues.append(f"Invalid file type: {file_ext} not in {allowed_extensions}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "filename": filename,
            "size_mb": size_mb,
        }


__all__ = ["SecurityValidator", "SecurityIssue", "SecurityLevel"]
