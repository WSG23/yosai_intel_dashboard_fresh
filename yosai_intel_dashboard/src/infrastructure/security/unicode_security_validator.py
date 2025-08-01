#!/usr/bin/env python3
"""Enterprise Unicode Security System - FIXED IMPLEMENTATION
Addresses: Unicode surrogate vulnerabilities, encoding attacks, security hardening
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd

from yosai_intel_dashboard.src.core.exceptions import SecurityError


class SecurityThreatLevel(Enum):
    """Security threat levels for Unicode validation"""

    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    CRITICAL = "critical"


@dataclass
class UnicodeSecurityConfig:
    """Configuration for Unicode security validation"""

    strict_mode: bool = True
    remove_surrogates: bool = True
    normalize_form: str = "NFKC"
    max_input_length: int = 50_000
    allow_emoji: bool = True
    allow_special_chars: bool = False
    log_violations: bool = True


class UnicodeSecurityValidator:
    """Enterprise-grade Unicode security validator

    Fixes:
    - Comprehensive surrogate pair detection and handling
    - Encoding attack prevention
    - Malicious pattern detection
    - Memory-safe processing
    """

    DANGEROUS_PATTERNS = [
        re.compile(r"[\u202A-\u202E]"),
        re.compile(r"[\u2066-\u2069]"),
        re.compile(r"[\uFDD0-\uFDEF]"),
        re.compile(r"[\uFFFE\uFFFF]"),
        re.compile(r"[\u0000-\u0008\u000B\u000C\u000E-\u001F]"),
        re.compile(r"[\u007F-\u009F]"),
    ]

    SURROGATE_PATTERNS = [
        re.compile(r"[\uD800-\uDBFF]"),
        re.compile(r"[\uDC00-\uDFFF]"),
        re.compile(r"[\uD800-\uDFFF]"),
    ]

    BOM_PATTERN = re.compile(r"[\uFEFF\uFFFE]")

    def __init__(
        self,
        config: Optional[UnicodeSecurityConfig] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config = config or UnicodeSecurityConfig()
        self.logger = logger or logging.getLogger(__name__)
        self._compile_security_patterns()

    def _compile_security_patterns(self) -> None:
        self.script_mixing_patterns = [
            (re.compile(r"[\u0020-\u007F]"), "latin"),
            (re.compile(r"[\u0080-\u024F]"), "latin_ext"),
            (re.compile(r"[\u0400-\u04FF]"), "cyrillic"),
            (re.compile(r"[\u0590-\u05FF]"), "hebrew"),
            (re.compile(r"[\u0600-\u06FF]"), "arabic"),
            (re.compile(r"[\u4E00-\u9FFF]"), "cjk"),
        ]

    # ------------------------------------------------------------------
    def validate_and_sanitize(self, input_data: Any) -> str:
        """Validate and sanitize ``input_data`` returning safe text."""

        try:
            text = self._safe_string_conversion(input_data)

            if len(text) > self.config.max_input_length:
                if self.config.strict_mode:
                    raise SecurityError(
                        f"Input exceeds maximum length: {self.config.max_input_length}"
                    )
                text = text[: self.config.max_input_length]
                self.logger.warning("Input truncated due to length limit")

            threat_level = self._assess_threat_level(text)
            if threat_level == SecurityThreatLevel.CRITICAL:
                if self.config.strict_mode:
                    raise SecurityError("Critical Unicode security threat detected")
                self.logger.error(
                    "Critical Unicode threat detected - sanitizing aggressively"
                )
                return self._emergency_sanitization(text)

            sanitized = self._sanitization_pipeline(text)

            if self._contains_dangerous_patterns(sanitized):
                if self.config.strict_mode:
                    raise SecurityError(
                        "Sanitization failed - dangerous patterns remain"
                    )
                sanitized = self._emergency_sanitization(sanitized)

            return sanitized

        except SecurityError:
            raise
        except Exception as exc:  # pragma: no cover - best effort
            self.logger.error(f"Unicode validation failed: {exc}")
            if self.config.strict_mode:
                raise SecurityError(f"Unicode validation error: {exc}")
            return self._emergency_sanitization(str(input_data))

    # ------------------------------------------------------------------
    def _safe_string_conversion(self, input_data: Any) -> str:
        if input_data is None:
            return ""
        if isinstance(input_data, str):
            return input_data
        if isinstance(input_data, bytes):
            try:
                return input_data.decode("utf-8", errors="replace")
            except Exception:
                return input_data.decode("latin-1", errors="replace")
        try:
            return str(input_data)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning(f"String conversion failed: {exc}")
            return "INVALID_INPUT"

    # ------------------------------------------------------------------
    def _assess_threat_level(self, text: str) -> SecurityThreatLevel:
        threat_score = 0

        if self._contains_surrogates(text):
            threat_score += 30

        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(text):
                threat_score += 25

        if self._has_script_mixing(text):
            threat_score += 15

        non_printable_ratio = self._calculate_non_printable_ratio(text)
        if non_printable_ratio > 0.1:
            threat_score += 20

        if self._has_encoding_exploits(text):
            threat_score += 40

        if threat_score >= 70:
            return SecurityThreatLevel.CRITICAL
        if threat_score >= 50:
            return SecurityThreatLevel.MALICIOUS
        if threat_score >= 25:
            return SecurityThreatLevel.SUSPICIOUS
        return SecurityThreatLevel.SAFE

    # ------------------------------------------------------------------
    def _contains_surrogates(self, text: str) -> bool:
        for pattern in self.SURROGATE_PATTERNS:
            if pattern.search(text):
                return True
        return False

    # ------------------------------------------------------------------
    def _contains_dangerous_patterns(self, text: str) -> bool:
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(text):
                return True
        return False

    # ------------------------------------------------------------------
    def _has_script_mixing(self, text: str) -> bool:
        detected_scripts = set()
        for char in text:
            if char.isspace() or char.isdigit():
                continue
            for pattern, script in self.script_mixing_patterns:
                if pattern.search(char):
                    detected_scripts.add(script)
                    break
        return len(detected_scripts) > 2

    # ------------------------------------------------------------------
    def _calculate_non_printable_ratio(self, text: str) -> float:
        if not text:
            return 0.0
        non_printable_count = sum(1 for c in text if not c.isprintable())
        return non_printable_count / len(text)

    # ------------------------------------------------------------------
    def _has_encoding_exploits(self, text: str) -> bool:
        try:
            encoded = text.encode("utf-8")
            decoded = encoded.decode("utf-8")
            if text != decoded:
                return True
        except Exception:
            return True

        try:
            nfc = unicodedata.normalize("NFC", text)
            nfd = unicodedata.normalize("NFD", text)
            nfkc = unicodedata.normalize("NFKC", text)
            nfkd = unicodedata.normalize("NFKD", text)
            forms = [nfc, nfd, nfkc, nfkd]
            if len(set(forms)) > 2:
                return True
        except Exception:
            return True

        return False

    # ------------------------------------------------------------------
    def _sanitization_pipeline(self, text: str) -> str:
        if self.config.remove_surrogates:
            text = self._remove_surrogates(text)
        text = self._remove_dangerous_patterns(text)
        text = self.BOM_PATTERN.sub("", text)
        try:
            text = unicodedata.normalize(self.config.normalize_form, text)
        except Exception as exc:  # pragma: no cover - best effort
            self.logger.warning(f"Unicode normalization failed: {exc}")
        text = self._remove_control_characters(text)
        try:
            text.encode("utf-8")
        except UnicodeEncodeError:
            text = text.encode("utf-8", errors="replace").decode("utf-8")
        return text

    # ------------------------------------------------------------------
    def _remove_surrogates(self, text: str) -> str:
        for pattern in self.SURROGATE_PATTERNS:
            text = pattern.sub("", text)
        safe_chars: List[str] = []
        for char in text:
            code_point = ord(char)
            if 0xD800 <= code_point <= 0xDFFF:
                if self.config.log_violations:
                    self.logger.warning(
                        f"Removed surrogate character: U+{code_point:04X}"
                    )
                continue
            safe_chars.append(char)
        return "".join(safe_chars)

    # ------------------------------------------------------------------
    def _remove_dangerous_patterns(self, text: str) -> str:
        for pattern in self.DANGEROUS_PATTERNS:
            text = pattern.sub("", text)
        return text

    # ------------------------------------------------------------------
    def _remove_control_characters(self, text: str) -> str:
        safe_chars: List[str] = []
        for char in text:
            if char in " \t\n\r":
                safe_chars.append(char)
            elif char.isprintable():
                safe_chars.append(char)
            elif self.config.log_violations:
                self.logger.debug(f"Removed control character: U+{ord(char):04X}")
        return "".join(safe_chars)

    # ------------------------------------------------------------------
    def _emergency_sanitization(self, text: str) -> str:
        safe_chars: List[str] = []
        for char in text:
            if 32 <= ord(char) <= 126 or char in " \t\n\r":
                safe_chars.append(char)
        result = "".join(safe_chars)
        if self.config.log_violations:
            self.logger.error(
                f"Emergency sanitization applied. Original length: {len(text)}, Sanitized: {len(result)}"
            )
        return result or "SANITIZED_CONTENT"

    # ------------------------------------------------------------------
    def validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        try:
            estimated_memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            if estimated_memory_mb > 500:
                return self._validate_dataframe_chunked(df)
            return self._validate_dataframe_full(df)
        except Exception as exc:  # pragma: no cover - best effort
            self.logger.error(f"DataFrame validation failed: {exc}")
            if self.config.strict_mode:
                raise SecurityError(f"DataFrame validation error: {exc}")
            return df

    # ------------------------------------------------------------------
    def _validate_dataframe_full(self, df: pd.DataFrame) -> pd.DataFrame:
        df_sanitized = df.copy()
        string_columns = df_sanitized.select_dtypes(include=["object"]).columns
        for col in string_columns:
            df_sanitized[col] = df_sanitized[col].apply(
                lambda x: self.validate_and_sanitize(x) if pd.notna(x) else x
            )
        return df_sanitized

    # ------------------------------------------------------------------
    def _validate_dataframe_chunked(
        self, df: pd.DataFrame, chunk_size: int = 10000
    ) -> pd.DataFrame:
        sanitized_chunks = []
        total_chunks = len(df) // chunk_size + (1 if len(df) % chunk_size else 0)
        self.logger.info(
            f"Processing DataFrame in {total_chunks} chunks of {chunk_size} rows"
        )
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i : i + chunk_size].copy()
            string_columns = chunk.select_dtypes(include=["object"]).columns
            for col in string_columns:
                chunk[col] = chunk[col].apply(
                    lambda x: self.validate_and_sanitize(x) if pd.notna(x) else x
                )
            sanitized_chunks.append(chunk)
        return pd.concat(sanitized_chunks, ignore_index=True)

    # ------------------------------------------------------------------
    def generate_security_report(self, text: str) -> Dict[str, Any]:
        report = {
            "input_length": len(text),
            "threat_level": self._assess_threat_level(text).value,
            "contains_surrogates": self._contains_surrogates(text),
            "contains_dangerous_patterns": self._contains_dangerous_patterns(text),
            "has_script_mixing": self._has_script_mixing(text),
            "non_printable_ratio": self._calculate_non_printable_ratio(text),
            "has_encoding_exploits": self._has_encoding_exploits(text),
            "security_issues": [],
        }

        if report["contains_surrogates"]:
            report["security_issues"].append("Contains Unicode surrogate characters")

        if report["contains_dangerous_patterns"]:
            report["security_issues"].append("Contains dangerous Unicode patterns")

        if report["has_script_mixing"]:
            report["security_issues"].append("Potential script mixing attack")

        if report["non_printable_ratio"] > 0.1:
            report["security_issues"].append("High ratio of non-printable characters")

        if report["has_encoding_exploits"]:
            report["security_issues"].append("Potential encoding-based exploit")

        return report


def create_unicode_validator(
    strict_mode: bool = True, remove_surrogates: bool = True
) -> UnicodeSecurityValidator:
    config = UnicodeSecurityConfig(
        strict_mode=strict_mode,
        remove_surrogates=remove_surrogates,
    )
    return UnicodeSecurityValidator(config=config)


def sanitize_for_utf8(input_data: Any) -> str:
    validator = UnicodeSecurityValidator()
    return validator.validate_and_sanitize(input_data)


def detect_surrogate_pairs(text: Any) -> bool:
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return False
    for char in text:
        code_point = ord(char)
        if 0xD800 <= code_point <= 0xDFFF:
            return True
    return False


__all__ = [
    "UnicodeSecurityValidator",
    "UnicodeSecurityConfig",
    "SecurityThreatLevel",
    "SecurityError",
    "create_unicode_validator",
    "sanitize_for_utf8",
    "detect_surrogate_pairs",
]
