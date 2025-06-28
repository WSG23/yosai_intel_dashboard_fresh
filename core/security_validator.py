"""
Enhanced Security Validation for Yōsai Intel Dashboard
Implements comprehensive input validation and security checks
"""
import re
import os
import hashlib
import secrets
from typing import Dict, Any, List

from utils.unicode_handler import sanitize_unicode_input
from dataclasses import dataclass
from enum import Enum


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

    # Compiled patterns for performance
    SQL_PATTERNS = [
        re.compile(r"(\bunion\b.*\bselect\b)", re.IGNORECASE),
        re.compile(r"(\bor\b.*=.*\bor\b)", re.IGNORECASE),
        re.compile(r"(--|\#|\/\*|\*\/)", re.IGNORECASE),
        re.compile(r"(\bxp_cmdshell\b|\bsp_executesql\b)", re.IGNORECASE),
        re.compile(r"(;\s*(drop|delete|truncate|alter)\b)", re.IGNORECASE)
    ]

    XSS_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"<iframe[^>]*>", re.IGNORECASE),
        re.compile(r"vbscript:", re.IGNORECASE)
    ]

    PATH_PATTERNS = [
        re.compile(r"\.\.\/"),
        re.compile(r"\.\.\\"),
        re.compile(r"%2e%2e%2f", re.IGNORECASE),
        re.compile(r"\.\.%2f", re.IGNORECASE)
    ]

    def validate_input(self, value: str, field_name: str = "input") -> Dict[str, Any]:
        """Comprehensive input validation"""
        value = sanitize_unicode_input(value)
        issues: List[SecurityIssue] = []

        # Check SQL injection
        for pattern in self.SQL_PATTERNS:
            if pattern.search(value):
                issues.append(SecurityIssue(
                    level=SecurityLevel.CRITICAL,
                    message="Potential SQL injection detected",
                    field=field_name,
                    recommendation="Remove SQL keywords and special characters"
                ))
                break

        # Check XSS
        for pattern in self.XSS_PATTERNS:
            if pattern.search(value):
                issues.append(SecurityIssue(
                    level=SecurityLevel.HIGH,
                    message="Potential XSS detected",
                    field=field_name,
                    recommendation="HTML encode user input"
                ))
                break

        # Check path traversal
        for pattern in self.PATH_PATTERNS:
            if pattern.search(value):
                issues.append(SecurityIssue(
                    level=SecurityLevel.MEDIUM,
                    message="Potential path traversal detected",
                    field=field_name,
                    recommendation="Validate file paths and restrict access"
                ))
                break

        # Sanitize input
        sanitized = self._sanitize_input(value)

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'sanitized': sanitized,
            'severity': max((issue.level for issue in issues), default=SecurityLevel.LOW)
        }

    def _sanitize_input(self, value: str) -> str:
        """Sanitize input by encoding dangerous characters"""
        value = sanitize_unicode_input(value)
        # HTML entity encoding
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;'
        }

        sanitized = value
        for char, entity in replacements.items():
            sanitized = sanitized.replace(char, entity)

        return sanitized

    @staticmethod
    def generate_secure_secret(length: int = 32) -> str:
        """Generate cryptographically secure secret key"""
        return secrets.token_hex(length)

    @staticmethod
    def validate_file_upload(filename: str, content: bytes, max_size_mb: int = 10) -> Dict[str, Any]:
        """Validate file uploads for security"""
        issues: List[str] = []

        # Check file size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > max_size_mb:
            issues.append(f"File too large: {size_mb:.1f}MB > {max_size_mb}MB")

        # Check filename
        if '..' in filename or '/' in filename or '\\' in filename:
            issues.append("Invalid filename: contains path traversal characters")

        # Check file extension
        allowed_extensions = {'.csv', '.json', '.xlsx', '.xls'}
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            issues.append(f"Invalid file type: {file_ext} not in {allowed_extensions}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'filename': filename,
            'size_mb': size_mb
        }

__all__ = ["SecurityValidator", "SecurityIssue", "SecurityLevel"]
