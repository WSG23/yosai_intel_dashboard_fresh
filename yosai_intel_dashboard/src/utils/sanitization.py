import bleach
import re
from pathlib import Path

__all__ = ["sanitize_text", "sanitize_label", "sanitize_filename"]


def sanitize_text(value: str) -> str:
    """Return *value* stripped of any unsafe HTML tags."""
    return bleach.clean(value or "", strip=True)


def sanitize_label(value: str) -> str:
    """Sanitize metric label values to prevent injection."""
    return bleach.clean(value or "", strip=True)


def sanitize_filename(value: str) -> str:
    """Return a safe filesystem-friendly version of ``value``.

    The filename is cleaned of HTML tags and path separators. ``ValueError``
    is raised for empty or unsafe names to prevent XSS or path traversal
    attacks.
    """

    if ".." in value or "/" in value or "\\" in value:
        raise ValueError("Invalid filename")
    cleaned = sanitize_text(value)
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", cleaned)
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("Invalid filename")
    # Ensure no path separators remain after cleaning
    if Path(cleaned).name != cleaned:
        raise ValueError("Invalid filename")
    return cleaned
