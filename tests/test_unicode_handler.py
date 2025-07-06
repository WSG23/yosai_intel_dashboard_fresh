import pytest

from config.unicode_handler import UnicodeQueryHandler


def test_safe_encode_query_surrogates():
    text = "test" + chr(0xD800)
    result = UnicodeQueryHandler.safe_encode_query(text)
    assert isinstance(result, str)
    assert "\ufffd" in result


def test_safe_encode_params_nested():
    params = {"a": ["b", {"c": "d" + chr(0xDCFF)}]}
    encoded = UnicodeQueryHandler.safe_encode_params(params)
    assert encoded["a"][1]["c"].endswith("\ufffd")
