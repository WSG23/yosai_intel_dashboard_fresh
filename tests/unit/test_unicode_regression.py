import pandas as pd
import pytest

from yosai_intel_dashboard.src.core.unicode import UnicodeProcessor, sanitize_dataframe, sanitize_unicode_input


def test_sanitize_unicode_input_normalizes_and_replaces():
    text = "ＡB" + "\ud800"
    result = sanitize_unicode_input(text)
    assert result == "AB"


def test_sanitize_unicode_input_handles_bytes():
    data = b"\xff\xfe\xfd"
    out = sanitize_unicode_input(data)
    assert isinstance(out, str)


def test_sanitize_dataframe_normalizes_columns_and_values():
    df = pd.DataFrame({"Ｃ": ["Ｄ" + "\udfff"]})
    cleaned = sanitize_dataframe(df)
    assert list(cleaned.columns) == ["C"]
    assert cleaned.iloc[0, 0] == "D"
