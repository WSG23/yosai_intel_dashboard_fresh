"""Minimal security service used for dependency injection."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict

from config.dynamic_config import dynamic_config
from core.unicode_utils import sanitize_unicode_input
from core.security import RateLimiter

SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9._\- ]{1,100}$")
ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}


class SecurityService:
    """Basic placeholder security service."""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.input_validation_enabled = False
        self.rate_limiter: RateLimiter | None = None
        self.file_validation_enabled = False
        self.events: list[Dict[str, Any]] = []

    def enable_input_validation(self) -> None:
        self.input_validation_enabled = True
        self.logger.info("Input validation enabled")

    def enable_rate_limiting(self) -> None:
        self.rate_limiter = RateLimiter(
            dynamic_config.security.rate_limit_requests,
            dynamic_config.security.rate_limit_window_minutes,
        )
        self.logger.info(
            "Rate limiting enabled: %s req / %s min",
            dynamic_config.security.rate_limit_requests,
            dynamic_config.security.rate_limit_window_minutes,
        )

    def enable_file_validation(self) -> None:
        self.file_validation_enabled = True
        self.logger.info("File validation enabled")

    def validate_file(self, filename: str, size: int) -> Dict[str, Any]:
        filename = sanitize_unicode_input(filename)
        issues: list[str] = []

        max_size_bytes = dynamic_config.security.max_upload_mb * 1024 * 1024
        if size > max_size_bytes:
            issues.append("File too large")

        if not SAFE_FILENAME_RE.fullmatch(filename):
            issues.append("Invalid filename")

        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            issues.append(f"Unsupported file type: {ext}")

        valid = len(issues) == 0
        return {"valid": valid, "issues": issues}

    def log_file_processing_event(
        self, filename: str, success: bool, error: str | None = None
    ) -> None:
        event = {
            "filename": filename,
            "success": success,
            "error": error,
        }
        self.events.append(event)
        if success:
            self.logger.info("Processed file %s", filename)
        else:
            self.logger.warning("File processing failed for %s: %s", filename, error)

    def get_security_status(self) -> Dict[str, Any]:
        return {
            "input_validation": self.input_validation_enabled,
            "rate_limiting": self.rate_limiter is not None,
            "file_validation": self.file_validation_enabled,
        }


__all__ = ["SecurityService"]
