"""Factories for creating validators based on configuration."""

from __future__ import annotations

from typing import Callable, Mapping

from .core import ValidationResult
from .file_validator import FileValidator
from .security_validator import SecurityValidator, SQLRule, XSSRule


def create_security_validator(
    config: Mapping[str, bool] | None = None,
    *,
    secret_scan_hook: Callable[[ValidationResult], None] | None = None,
    anomaly_hook: Callable[[str, ValidationResult], None] | None = None,
) -> SecurityValidator:
    if config is None:
        from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
            dynamic_config,
        )

        cfg = dynamic_config.uploads.VALIDATOR_RULES
    else:
        cfg = config
    rules = []
    if cfg.get("xss", True):
        rules.append(XSSRule())
    if cfg.get("sql_injection", True):
        rules.append(SQLRule())
    return SecurityValidator(
        rules,
        secret_scan_hook=secret_scan_hook,
        anomaly_hook=anomaly_hook,
    )


def create_file_validator(max_size_mb: int | None = None) -> FileValidator:
    return FileValidator(max_size_mb)
