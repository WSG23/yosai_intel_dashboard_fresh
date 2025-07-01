import pytest

from plugins.lazystring_fix_plugin import sanitize_lazystring
from config.constants import SecurityLimits


def _contains_surrogate(text: str) -> bool:
    return any(0xD800 <= ord(ch) <= 0xDFFF for ch in text)


def test_surrogate_pair_removed():
    text = "\ud800\udc00test"
    result = sanitize_lazystring(text)
    assert not _contains_surrogate(result)
    assert "test" in result


def test_lone_surrogate_removed():
    text = "start\ud800end"
    result = sanitize_lazystring(text)
    assert not _contains_surrogate(result)


def test_unicode_normalization():
    # Angstrom sign -> Latin capital A with ring above
    text = "\u212B"
    result = sanitize_lazystring(text)
    assert result == "\u00C5"


def test_nested_structures_and_types():
    try:
        from flask_babel import lazy_gettext
    except Exception:
        pytest.skip("flask_babel not available")

    data = {
        "msg": lazy_gettext("hello"),
        "items": [1, lazy_gettext("bye"), {"again": lazy_gettext("again")}],
    }
    sanitized = sanitize_lazystring(data)
    assert sanitized["msg"] == "hello"
    assert sanitized["items"][1] == "bye"
    assert sanitized["items"][2]["again"] == "again"
    assert sanitized["items"][0] == 1


def test_long_string_performance():
    text = "a" * SecurityLimits.MAX_INPUT_STRING_LENGTH_CHARACTERS
    result = sanitize_lazystring(text)
    assert result == text
