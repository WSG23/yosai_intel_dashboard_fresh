import pandas as pd

from utils.upload_store import UploadedDataStore


def test_pkl_migration(tmp_path):
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    pkl_path = tmp_path / "legacy.csv.pkl"
    df.to_pickle(pkl_path)

    store = UploadedDataStore(storage_dir=tmp_path)

    parquet_path = tmp_path / "legacy.csv.parquet"
    assert parquet_path.exists()
    assert not pkl_path.exists()
    assert store.get_filenames() == ["legacy.csv"]
    pd.testing.assert_frame_equal(store.get_all_data()["legacy.csv"], df)
    info = store.get_file_info()["legacy.csv"]
    assert info["rows"] == 2
    assert info["columns"] == 2
