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


def sanitize_unicode_input(value: str) -> str:
    """Handle Unicode surrogate characters safely."""
    try:
        if not isinstance(value, str):
            value = str(value)

        # Encode to ASCII with replacement to ensure the result contains
        # only safe characters.  Non-ASCII characters will be substituted with
        # ``?`` so the decoded text remains readable and length is preserved.
        cleaned = value.encode("ascii", errors="replace").decode("ascii")

        # Validate surrogate pairs and replace any remaining invalid ones with
        # the Unicode replacement character. ``errors="replace"`` above should
        # handle most cases but this is a defensive check.
        for char in cleaned:
            if 0xD800 <= ord(char) <= 0xDFFF:
                cleaned = cleaned.replace(char, "\ufffd")

        return cleaned
    except (UnicodeError, UnicodeDecodeError) as exc:  # pragma: no cover - safety
        logger.warning("Unicode sanitization failed: %s", exc)
        # Fall back to ASCII-safe text if UTF-8 processing fails
        return value.encode("ascii", errors="replace").decode("ascii")

