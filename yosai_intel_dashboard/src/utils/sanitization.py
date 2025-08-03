import bleach

__all__ = ["sanitize_text", "sanitize_label"]


def sanitize_text(value: str) -> str:
    """Return *value* stripped of any unsafe HTML tags."""
    return bleach.clean(value or "", strip=True)


def sanitize_label(value: str) -> str:
    """Sanitize metric label values to prevent injection."""
    return bleach.clean(value or "", strip=True)
