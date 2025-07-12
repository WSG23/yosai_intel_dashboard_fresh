from utils import sanitize_unicode_input


def test_utils_exposes_sanitize_unicode_input():
    text = "A" + "\ud800" + "B"
    assert sanitize_unicode_input(text) == "AB"
