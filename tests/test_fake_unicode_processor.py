import pandas as pd

from tests.fake_unicode_processor import FakeUnicodeProcessor


def test_fake_processor_basic():
    proc = FakeUnicodeProcessor()
    assert proc.clean_surrogate_chars("A\ud800B") == "AB"
    df = pd.DataFrame({"=c": ["x\ud800"]})
    cleaned = proc.sanitize_dataframe(df)
    assert list(cleaned.columns) == ["c"]
    assert cleaned.iloc[0, 0] == "x"
