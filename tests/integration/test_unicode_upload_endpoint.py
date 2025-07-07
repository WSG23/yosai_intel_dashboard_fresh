from pathlib import Path

import pandas as pd

from security.unicode_security_handler import UnicodeSecurityHandler
from core.unicode_processor import safe_unicode_encode


class SimpleStore:
    def __init__(self, path):
        self.data = {}
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def add_file(self, name: str, df: pd.DataFrame) -> None:
        self.data[name] = df

    def load_dataframe(self, name: str) -> pd.DataFrame:
        return self.data[name]

    def wait_for_pending_saves(self) -> None:  # compatibility
        pass


def test_upload_dataframe_sanitization():
    df = pd.DataFrame({"c\ud83d": ["v\ude00"]})
    cleaned = UnicodeSecurityHandler.sanitize_dataframe(df)
    assert list(cleaned.columns) == ["c"]
    assert cleaned.iloc[0, 0] == "v"


def test_non_ascii_filename_persistence(tmp_path):
    df = pd.DataFrame({"a": [1]})
    filename = "данные\ud83d.csv"
    safe_name = safe_unicode_encode(filename)

    store = SimpleStore(tmp_path)
    store.add_file(safe_name, df)

    assert safe_name.endswith("данные.csv")
    pd.testing.assert_frame_equal(store.load_dataframe(safe_name), df)
