"""Unified Unicode processing helpers.

This subpackage bundles text, SQL and security utilities.  Use the
factory helpers to obtain the appropriate processor:

>>> from core.unicode import get_text_processor
>>> processor = get_text_processor()
>>> safe = processor.safe_encode_text("example")

Simple class aliases (:class:`TextProcessor`, :class:`SQLProcessor`,
and :class:`SecurityProcessor`) remain available for backward
compatibility.
"""

from utils.unicode_utils import (
    UnicodeProcessor,
    ChunkedUnicodeProcessor,
)
from config.unicode_handler import UnicodeQueryHandler
from security.unicode_security_handler import UnicodeSecurityHandler

# ---------------------------------------------------------------------------
# Backward compatible aliases
# ---------------------------------------------------------------------------
TextProcessor = UnicodeProcessor
SQLProcessor = UnicodeQueryHandler
SecurityProcessor = UnicodeSecurityHandler

# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def get_text_processor() -> type[TextProcessor]:
    """Return the Unicode text processor class."""
    return TextProcessor


def get_sql_processor() -> type[SQLProcessor]:
    """Return the SQL Unicode processor class."""
    return SQLProcessor


def get_security_processor() -> type[SecurityProcessor]:
    """Return the security Unicode processor class."""
    return SecurityProcessor


__all__ = [
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    "UnicodeQueryHandler",
    "UnicodeSecurityHandler",
    "TextProcessor",
    "SQLProcessor",
    "SecurityProcessor",
    "get_text_processor",
    "get_sql_processor",
    "get_security_processor",
]
