import pandas as pd

from services.data_processing.processor import Processor


def test_get_processed_database_basic(monkeypatch):
    loader = Processor()
    uploaded = {
        "sample.csv": pd.DataFrame(
            {
                "ts": ["2024-01-01"],
                "door_id": ["d1"],
                "person_id": ["u1"],
            }
        )
    }
    mappings = {
        "fp": {
            "filename": "sample.csv",
            "column_mappings": {"ts": "timestamp"},
            "device_mappings": {"d1": {"location": "HQ"}},
        }
    }
    monkeypatch.setattr(loader, "_get_uploaded_data", lambda: uploaded)
    monkeypatch.setattr(loader, "_load_consolidated_mappings", lambda: mappings)

    df, meta = loader.get_processed_database()
    assert "timestamp" in df.columns
    assert "location" in df.columns
    assert meta["processed_files"] == 1
    assert meta["total_records"] == 1
