import pytest

try:
    from config.unicode_handler import UnicodeQueryHandler as UnicodeHandler
except Exception:  # pragma: no cover - fallback name
    from config.unicode_handler import UnicodeQueryHandler as UnicodeHandler


def test_surrogate_pair_encoding():
    emoji = chr(0xD83D) + chr(0xDC36)  # dog face
    result = UnicodeHandler.safe_encode_query(emoji)
    assert result == emoji


def test_invalid_surrogate_handling():
    text = "bad" + chr(0xD800)
    result = UnicodeHandler.safe_encode_query(text)
    assert "\ufffd" in result
    assert chr(0xD800) not in result
