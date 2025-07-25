import pandas as pd

from yosai_intel_dashboard.src.core.unicode import (
    UnicodeProcessor,
    safe_encode_text,
    sanitize_dataframe,
)


def test_clean_dataframe_removes_surrogates():
    df = pd.DataFrame(
        {"bad" + chr(0xD800) + "col": ["A" + chr(0xDC00), "B" + chr(0xDFFF)]}
    )
    cleaned = sanitize_dataframe(df)
    assert list(cleaned.columns) == ["badcol"]
    assert list(cleaned.iloc[:, 0]) == ["A", "B"]


def test_safe_encode_text_returns_utf8_without_surrogates():
    text = "X" + chr(0xD800) + "Y"
    bytes_value = text.encode("utf-8", "surrogatepass")

    for value in (text, bytes_value):
        result = safe_encode_text(value)
        assert isinstance(result, str)
        assert result == "XY"
        assert not any(0xD800 <= ord(ch) <= 0xDFFF for ch in result)
