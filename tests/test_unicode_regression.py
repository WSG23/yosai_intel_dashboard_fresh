import pandas as pd
import pytest

from core.unicode import UnicodeProcessor
from security.unicode_security_processor import UnicodeSecurityProcessor


def test_sanitize_unicode_input_normalizes_and_replaces():
    text = "ＡB" + "\ud800"
    result = UnicodeSecurityProcessor.sanitize_unicode_input(text)
    assert result == "AB" + UnicodeProcessor.REPLACEMENT_CHAR


def test_sanitize_unicode_input_handles_bytes():
    data = b"\xff\xfe\xfd"
    out = UnicodeSecurityProcessor.sanitize_unicode_input(data)
    assert isinstance(out, str)


def test_sanitize_dataframe_normalizes_columns_and_values():
    df = pd.DataFrame({"Ｃ": ["Ｄ" + "\udfff"]})
    cleaned = UnicodeSecurityProcessor.sanitize_dataframe(df)
    assert list(cleaned.columns) == ["C"]
    assert cleaned.iloc[0, 0] == "D"
