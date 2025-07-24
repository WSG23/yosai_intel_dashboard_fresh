"""Unified Unicode utilities package."""

from .core import UnicodeProcessor

__all__ = [
    "UnicodeProcessor",
    "UnicodeValidator",
    "UnicodeSanitizer",
    "UnicodeEncoder",
]


def __getattr__(name: str):
    if name == "UnicodeValidator":
        from importlib import import_module

        return import_module("security.unicode_security_validator").UnicodeSecurityValidator
    if name == "UnicodeSanitizer":
        from core import unicode as _u

        return _u.sanitize_unicode_input
    if name == "UnicodeEncoder":
        from core import unicode as _u

        return _u.UnicodeSQLProcessor
    raise AttributeError(name)

