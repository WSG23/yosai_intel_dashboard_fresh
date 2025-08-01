"""Custom security-related exceptions and helpers."""

from yosai_intel_dashboard.src.core.exceptions import ValidationError as CoreValidationError


class SecurityViolation(Exception):
    """Raised for detected attacks."""


class ValidationError(CoreValidationError):  # pragma: no cover - thin alias
    """Alias for :class:`core.exceptions.ValidationError`."""
