from yosai_intel_dashboard.src.core.unicode import safe_unicode_decode, sanitize_for_utf8


def test_safe_unicode_decode_handles_surrogates():
    data = b"A\xed\xa0\x80B"  # contains lone high surrogate
    assert safe_unicode_decode(data) == "AB"


def test_sanitize_for_utf8_normalizes_and_strips():
    text = "A" + "\ud800" + "B" + "\ufeff" + "Ｃ"
    assert sanitize_for_utf8(text) == "ABC"
