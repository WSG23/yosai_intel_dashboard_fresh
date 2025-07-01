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

        # Remove lone surrogates that can't be encoded
        cleaned = value.encode("utf-8", errors="ignore").decode("utf-8")

        # Validate surrogate pairs and replace invalid ones with the
        # Unicode replacement character.  ``errors="ignore"`` above will
        # drop lone surrogates, but malformed pairs may still exist when
        # ``surrogatepass`` decoding was used earlier.
        for char in cleaned:
            if 0xD800 <= ord(char) <= 0xDFFF:
                cleaned = cleaned.replace(char, "\ufffd")

        return cleaned
    except (UnicodeError, UnicodeDecodeError):  # pragma: no cover - safety
        return "\ufffd"

