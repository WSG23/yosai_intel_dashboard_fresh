import pytest

from yosai_intel_dashboard.src.core.unicode import safe_unicode_decode


def test_removes_invalid_surrogates():
    data = b"A\xed\xa0\x80B"  # contains lone high surrogate D800
    assert safe_unicode_decode(data) == "AB"


def test_fallback_on_unicode_error():
    latin = "café".encode("latin-1")
    out = safe_unicode_decode(latin, "ascii")
    assert isinstance(out, str)
    assert out.startswith("caf")
