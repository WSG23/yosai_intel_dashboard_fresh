"""Advanced SQL injection prevention utilities."""

from __future__ import annotations

import logging
import re
import urllib.parse
from dataclasses import dataclass
from typing import Any, Optional, Tuple

import bleach
import sqlparse
from sqlparse import tokens as T

from core.security_patterns import SQL_INJECTION_PATTERNS
from .attack_detection import AttackDetection
from .validation_exceptions import ValidationError


class SQLSecurityLimits:
    """Default bounds for SQL security checks."""

    MAX_PARAMETER_LENGTH: int = 2048
    MAX_QUERY_LENGTH: int = 4096


@dataclass
class SQLSecurityConfig:
    """Configuration for SQL injection safeguards."""

    allowed_characters: str = r"[\w\s,._@()-]"
    max_length: int = SQLSecurityLimits.MAX_PARAMETER_LENGTH


class SQLInjectionPrevention:
    """Validate SQL parameters and statements."""

    def __init__(self, config: SQLSecurityConfig | None = None) -> None:
        self.config = config or SQLSecurityConfig()
        self.logger = logging.getLogger(__name__)
        self.attack_detection = AttackDetection()
        self._allowed_char_re = re.compile(self.config.allowed_characters)
        self._patterns = [re.compile(p, re.IGNORECASE) for p in SQL_INJECTION_PATTERNS]

    # ------------------------------------------------------------------
    def sanitize_parameter(self, value: Any) -> str:
        """Return a sanitized SQL parameter string."""
        text = str(value)
        if len(text) > self.config.max_length:
            self.logger.warning("SQL parameter too long")
            raise ValidationError("SQL parameter exceeds maximum length")

        # Whitelist allowed characters only
        cleaned = ''.join(ch for ch in text if self._allowed_char_re.match(ch))
        sanitized = bleach.clean(cleaned, strip=True)
        return sanitized

    # ------------------------------------------------------------------
    def validate_query_parameter(self, value: Any) -> str:
        """Validate and sanitize a single query parameter."""
        sanitized = self.sanitize_parameter(value)
        decoded = urllib.parse.unquote_plus(sanitized)
        to_check = decoded.lower()

        for pattern in self._patterns:
            if pattern.search(to_check):
                self.attack_detection.record(f"SQL injection attempt: {decoded}")
                raise ValidationError("Potential SQL injection detected")
        return sanitized

    # ------------------------------------------------------------------
    def validate_sql_statement(self, sql: str) -> str:
        """Validate a full SQL statement."""
        sanitized = self.validate_query_parameter(sql)
        statements = sqlparse.parse(sanitized)

        if len(statements) != 1:
            self.attack_detection.record("Multiple SQL statements rejected")
            raise ValidationError("Multiple SQL statements are not allowed")

        stmt = statements[0]
        for token in stmt.flatten():
            if token.ttype in {T.Keyword.DDL, T.Keyword.DML} and token.value.upper() in {
                "DROP",
                "DELETE",
                "TRUNCATE",
                "ALTER",
                "GRANT",
            }:
                self.attack_detection.record(f"Dangerous SQL keyword: {token.value}")
                raise ValidationError("Dangerous SQL statement detected")
        return sanitized

    # ------------------------------------------------------------------
    def enforce_parameterization(self, statement: str, params: Optional[Tuple[Any, ...]]) -> None:
        """Ensure that placeholders and parameters match."""
        placeholder_count = statement.count("?")
        if placeholder_count == 0 and params:
            self.attack_detection.record("Parameters provided without placeholders")
            raise ValidationError("SQL placeholders missing")
        if placeholder_count and (not params or len(params) != placeholder_count):
            self.attack_detection.record("Mismatch between placeholders and parameters")
            raise ValidationError("Mismatch between SQL placeholders and parameters")


__all__ = ["SQLSecurityLimits", "SQLSecurityConfig", "SQLInjectionPrevention"]
