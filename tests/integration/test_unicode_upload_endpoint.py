import pandas as pd

from yosai_intel_dashboard.src.core.unicode import safe_unicode_encode
from yosai_intel_dashboard.src.infrastructure.security.unicode_security_handler import (
    UnicodeSecurityHandler,
)


def test_upload_dataframe_sanitization():
    df = pd.DataFrame({"c\ud83d": ["v\ude00"]})
    cleaned = UnicodeSecurityHandler.sanitize_dataframe(df)
    assert list(cleaned.columns) == ["c"]
    assert cleaned.iloc[0, 0] == "v"


def test_non_ascii_filename_persistence(fake_upload_storage):
    df = pd.DataFrame({"a": [1]})
    filename = "данные\ud83d.csv"
    safe_name = safe_unicode_encode(filename)

    store = fake_upload_storage
    store.add_file(safe_name, df)

    assert safe_name.endswith("данные.csv")
    pd.testing.assert_frame_equal(store.load_dataframe(safe_name), df)
