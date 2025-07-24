"""Factories for creating validators based on configuration."""
from __future__ import annotations

from typing import Mapping

from config.dynamic_config import dynamic_config

from .file_validator import FileValidator
from .security_validator import SQLRule, SecurityValidator, XSSRule


def create_security_validator(config: Mapping[str, bool] | None = None) -> SecurityValidator:
    cfg = config or dynamic_config.uploads.VALIDATOR_RULES
    rules = []
    if cfg.get("xss", True):
        rules.append(XSSRule())
    if cfg.get("sql_injection", True):
        rules.append(SQLRule())
    return SecurityValidator(rules)


def create_file_validator(max_size_mb: int | None = None) -> FileValidator:
    return FileValidator(max_size_mb)

