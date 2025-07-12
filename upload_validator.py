"""Validation helpers for uploaded files."""

from __future__ import annotations

from services.data_processing.unified_upload_validator import UnifiedUploadValidator
from upload_types import ValidationResult

UploadValidator = UnifiedUploadValidator

__all__ = ["UploadValidator", "ValidationResult"]
