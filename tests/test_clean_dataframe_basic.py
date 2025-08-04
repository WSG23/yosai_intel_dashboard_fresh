from __future__ import annotations

import importlib.util
import sys
import types
from datetime import datetime
from pathlib import Path

# Minimal pandas stub with just enough for our tests


class DataFrame:
    def __init__(self, data):
        self._data = data
        self.columns = list(data.keys())

    @property
    def empty(self):
        return len(self) == 0

    def dropna(self, how="any", axis=0):
        if axis == 0:
            rows = list(zip(*[self._data[c] for c in self.columns]))
            new_rows = [r for r in rows if not all(v is None for v in r)]
            new_data = {c: [r[i] for r in new_rows] for i, c in enumerate(self.columns)}
        else:
            new_data = {
                c: vals
                for c, vals in self._data.items()
                if not all(v is None for v in vals)
            }
        return DataFrame(new_data)

    def rename(self, columns):
        new_data = {columns.get(c, c): vals for c, vals in self._data.items()}
        return DataFrame(new_data)

    def __getitem__(self, item):
        if isinstance(item, list):
            return DataFrame({c: self._data[c] for c in item})
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value
        if key not in self.columns:
            self.columns.append(key)

    def __len__(self):
        return len(next(iter(self._data.values()))) if self._data else 0


def to_datetime(values, errors="coerce"):
    def parse(v):
        try:
            return datetime.fromisoformat(v)
        except Exception:
            return None

    if isinstance(values, list):
        return [parse(v) for v in values]
    return parse(values)


pd_stub = types.SimpleNamespace(DataFrame=DataFrame, to_datetime=to_datetime)
sys.modules["pandas"] = pd_stub

spec = importlib.util.spec_from_file_location(
    "upload_processing",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard/src/services/upload/upload_processing.py",
)
upload_processing = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(upload_processing)
UploadAnalyticsProcessor = upload_processing.UploadAnalyticsProcessor


def test_clean_uploaded_dataframe_maps_columns_and_parses_timestamp():
    df = DataFrame(
        {
            "Timestamp": ["2024-01-01 00:00:00"],
            "Person ID": ["u1"],
            "Token ID": ["t1"],
            "Device name": ["d1"],
            "Access result": ["Granted"],
        }
    )
    ua = UploadAnalyticsProcessor()
    cleaned = ua.clean_uploaded_dataframe(df)
    assert cleaned.columns == [
        "timestamp",
        "person_id",
        "token_id",
        "door_id",
        "access_result",
    ]
    assert isinstance(cleaned["timestamp"][0], datetime)


def test_clean_uploaded_dataframe_drops_empty_rows_and_columns():
    df = DataFrame(
        {
            "Timestamp": ["2024-01-01 00:00:00", None],
            "Person ID": ["u1", None],
            "Token ID": ["t1", None],
            "Device name": ["d1", None],
            "Access result": ["Granted", None],
            "EmptyCol": [None, None],
        }
    )
    ua = UploadAnalyticsProcessor()
    cleaned = ua.clean_uploaded_dataframe(df)
    assert cleaned.columns == [
        "timestamp",
        "person_id",
        "token_id",
        "door_id",
        "access_result",
    ]
    assert len(cleaned) == 1
