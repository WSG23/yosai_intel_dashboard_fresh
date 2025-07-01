import json
import pandas as pd
from datetime import datetime
from file_conversion.storage_manager import StorageManager


def test_migrate_pkl_to_parquet(tmp_path):
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    pkl_path = tmp_path / "sample.pkl"
    df.to_pickle(pkl_path)

    storage = StorageManager(base_dir=tmp_path / "converted")
    success, msg = storage.migrate_pkl_to_parquet(pkl_path)
    assert success, msg

    parquet_path = storage.base_dir / "sample.parquet"
    assert parquet_path.exists()
    loaded = pd.read_parquet(parquet_path)
    pd.testing.assert_frame_equal(loaded, df)

    metadata_path = storage.base_dir / "metadata.json"
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text())
    assert "sample.parquet" in metadata
    entry = metadata["sample.parquet"]
    assert entry["original_file"] == str(pkl_path)
    assert "converted_at" in entry
    # ensure ISO format timestamp
    datetime.fromisoformat(entry["converted_at"])
