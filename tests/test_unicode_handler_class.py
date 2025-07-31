import pytest

from yosai_intel_dashboard.src.infrastructure.config.unicode_handler import UnicodeHandler


def test_handler_encodes_query_surrogates():
    handler = UnicodeHandler()
    text = "SELECT" + chr(0xD800) + "1"
    result = handler.encode_query(text)
    assert result == "SELECT1"


def test_handler_clean_filename():
    handler = UnicodeHandler()
    name = "=bad" + chr(0xDC00) + ".csv"
    clean = handler.clean_filename(name)
    assert "bad" in clean and "\udc00" not in clean
