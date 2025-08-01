"""
Text utilities for safe text handling
"""

from typing import Any, Union

from yosai_intel_dashboard.src.core.unicode import clean_surrogate_chars


def safe_text(text: Union[str, Any]) -> str:
    """
    Return text safely, handling any babel objects or non-string types

    Args:
        text: Any text-like object or string

    Returns:
        str: Safe string representation
    """
    if text is None:
        return ""

    # Handle different types safely
    if hasattr(text, "__str__"):
        return clean_surrogate_chars(str(text))

    # Fallback for any other type
    return clean_surrogate_chars(repr(text))


def sanitize_text_for_dash(text: Union[str, Any]) -> str:
    """
    Sanitize text specifically for Dash components

    Args:
        text: Input text or object

    Returns:
        str: Dash-safe text
    """
    safe_str = safe_text(text)
    safe_str = clean_surrogate_chars(safe_str)

    # Remove any problematic characters that might cause JSON issues
    safe_str = safe_str.replace("\x00", "")  # Remove null bytes
    safe_str = safe_str.replace("\ufeff", "")  # Remove BOM

    return safe_str


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length

    Args:
        text: Input text
        max_length: Maximum length before truncation
        suffix: Suffix to add when truncated

    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


__all__ = ["safe_text", "sanitize_text_for_dash", "format_file_size", "truncate_text"]
