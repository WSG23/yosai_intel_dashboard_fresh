"""Unified Unicode utilities package."""

from .core import UnicodeProcessor

__all__ = [
    "UnicodeProcessor",
    "UnicodeValidator",
    "UnicodeSanitizer",
    "UnicodeEncoder",
    "UnicodeSQLProcessor",
]


def __getattr__(name: str):
    if name == "UnicodeValidator":
        from importlib import import_module

        return import_module(
            "security.unicode_security_validator"
        ).UnicodeSecurityValidator
    if name == "UnicodeSanitizer":
        from core import unicode as _u

        return _u.sanitize_unicode_input
    if name in {"UnicodeEncoder", "UnicodeSQLProcessor"}:
        from core import unicode as _u

        return _u.UnicodeSQLProcessor
    raise AttributeError(name)


class UnicodeQueryHandler:
    """Compatibility wrapper for safe SQL encoding."""

    @staticmethod
    def safe_encode_query(query: str) -> str:
        from core.unicode import UnicodeSQLProcessor

        return UnicodeSQLProcessor.encode_query(query)

    @staticmethod
    def safe_encode_params(params):
        if params is None:
            return None
        return tuple(
            UnicodeQueryHandler.safe_encode_query(p) if isinstance(p, str) else p
            for p in params
        )


__all__.append("UnicodeQueryHandler")


def clean_unicode_surrogates(text: str, replacement: str = "") -> str:
    """Compatibility shim for legacy imports."""
    from core.unicode import clean_surrogate_chars

    return clean_surrogate_chars(text, replacement)


__all__.append("clean_unicode_surrogates")
