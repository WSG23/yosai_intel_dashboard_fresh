"""Enhanced Unicode handling with surrogate character support."""

import logging
import unicodedata
import re

logger = logging.getLogger(__name__)


def safe_decode_with_unicode_handling(content: bytes, encoding: str = "utf-8") -> str:
    """Safely decode bytes with comprehensive Unicode handling."""
    try:
        text = content.decode(encoding, errors="replace")
        text = handle_surrogate_characters(text)
        return text
    except Exception as e:
        logger.warning(f"Unicode decode failed with {encoding}: {e}")
        return content.decode("latin-1", errors="replace")


def handle_surrogate_characters(text: str) -> str:
    """Handle Unicode surrogate characters that can't be encoded in UTF-8."""
    try:
        text = re.sub(r"[\uD800-\uDFFF]", "�", text)
        text = unicodedata.normalize("NFKC", text)
        text = text.encode("utf-8", errors="replace").decode("utf-8")
        return text
    except Exception as e:
        logger.warning(f"Surrogate character handling failed: {e}")
        return text.encode("utf-8", errors="replace").decode("utf-8")


def sanitize_unicode_input(text: str) -> str:
    """Sanitize Unicode input for safe processing."""
    if not isinstance(text, str):
        text = str(text)

    text = handle_surrogate_characters(text)

    text = "".join(
        char
        for char in text
        if unicodedata.category(char)[0] != "C" or char in "\t\n\r "
    )

    if len(text) > 10000:
        text = text[:10000] + "..."

    return text

