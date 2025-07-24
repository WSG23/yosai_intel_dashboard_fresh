import pandas as pd

from unicode_toolkit import UnicodeProcessor
from unicode_toolkit.pandas_integration import sanitize_dataframe
from unicode_toolkit.sql_safe import encode_query


def test_processor_basic():
    proc = UnicodeProcessor()
    assert proc.process("A\ud800B") == "AB"
    assert proc.clean_surrogate_chars("X\ud800Y") == "XY"


def test_dataframe_helper():
    df = pd.DataFrame({"=c\ud800": ["val\udfff"]})
    cleaned = sanitize_dataframe(df)
    assert list(cleaned.columns) == ["c"]
    assert cleaned.iloc[0, 0] == "val"


def test_sql_encoding():
    assert encode_query("SELECT 'a'\ud800") == "SELECT 'a'"
