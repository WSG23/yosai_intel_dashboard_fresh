"""Custom validation exceptions."""

class ValidationError(Exception):
    """Raised when validation fails."""

class SecurityViolation(Exception):
    """Raised for detected attacks."""
