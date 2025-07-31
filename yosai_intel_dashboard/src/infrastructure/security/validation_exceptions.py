"""Custom security-related exceptions and helpers."""

from core.exceptions import ValidationError as CoreValidationError


class SecurityViolation(Exception):
    """Raised for detected attacks."""


class ValidationError(CoreValidationError):  # pragma: no cover - thin alias
    """Alias for :class:`core.exceptions.ValidationError`."""
