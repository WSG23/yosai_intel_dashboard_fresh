import pytest

from yosai_intel_dashboard.src.core.unicode import sanitize_unicode_input


def test_sanitize_unicode_removes_surrogates():
    text = "A" + "\ud800" + "B" + "\udfff"
    result = sanitize_unicode_input(text)
    assert "\ud800" not in result
    assert "\udfff" not in result
    assert "A" in result and "B" in result


def test_sanitize_unicode_removes_bom():
    text = "\ufeffHello"
    assert sanitize_unicode_input(text) == "Hello"


def test_sanitize_unicode_handles_bad_str():
    class Bad:
        def __str__(self):
            raise UnicodeError("boom")

    output = sanitize_unicode_input(Bad())
    assert isinstance(output, str)
    assert output.isascii()
