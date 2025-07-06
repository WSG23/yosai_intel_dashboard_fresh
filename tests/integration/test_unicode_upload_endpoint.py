import pandas as pd

from security.unicode_security_handler import UnicodeSecurityHandler


def test_upload_dataframe_sanitization():
    df = pd.DataFrame({"c\ud83d": ["v\ude00"]})
    cleaned = UnicodeSecurityHandler.sanitize_dataframe(df)
    assert list(cleaned.columns) == ["c"]
    assert cleaned.iloc[0, 0] == "v"
