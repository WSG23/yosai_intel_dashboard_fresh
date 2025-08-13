import pytest

import pytest

try:
    from unicode_toolkit import safe_encode_text  # type: ignore
except Exception as exc:  # pragma: no cover - environment missing deps
    pytest.skip(f"unicode_toolkit unavailable: {exc}", allow_module_level=True)


def test_safe_encode_strips_newlines():
    assert safe_encode_text("bad\nname.csv") == "badname.csv"


def test_safe_encode_drops_prefix():
    assert safe_encode_text("=formula.csv") == "formula.csv"


def test_safe_encode_drops_unpaired_surrogate():
    assert safe_encode_text("bad\ud83dname.csv") == "badname.csv"
