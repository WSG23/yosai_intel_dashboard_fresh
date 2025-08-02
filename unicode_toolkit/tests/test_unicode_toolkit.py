import pandas as pd

from yosai_intel_dashboard.src.core.unicode import UnicodeProcessor, UnicodeSQLProcessor, sanitize_dataframe


def test_processor_basic():
    assert UnicodeProcessor.clean_text("A\ud800B") == "AB"
    assert UnicodeProcessor.clean_surrogate_chars("X\ud800Y") == "XY"


def test_dataframe_helper():
    df = pd.DataFrame({"=c\ud800": ["val\udfff"]})
    cleaned = sanitize_dataframe(df)
    assert list(cleaned.columns) == ["c"]
    assert cleaned.iloc[0, 0] == "val"


def test_sql_encoding():
    assert UnicodeSQLProcessor.encode_query("SELECT 'a'\ud800") == "SELECT 'a'"
