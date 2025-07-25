import pytest

from yosai_intel_dashboard.src.core.unicode import (
    UnicodeNormalizationError,
    detect_surrogate_pairs,
    normalize_unicode_safely,
    sanitize_for_utf8,
)


def test_normalize_unicode_safely_nfkc():
    text = "ＡＢＣ"
    assert normalize_unicode_safely(text) == "ABC"


def test_detect_surrogate_pairs():
    assert detect_surrogate_pairs("\ud83d\ude00")
    assert not detect_surrogate_pairs("hello")


def test_sanitize_for_utf8_removes_surrogates_and_normalizes():
    text = "A" + "\ud800" + "B" + "\ufeff" + "Ｃ"
    assert sanitize_for_utf8(text) == "ABC"
