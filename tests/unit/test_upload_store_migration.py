from tests.utils.builders import DataFrameBuilder
from yosai_intel_dashboard.src.utils.upload_store import UploadedDataStore


def test_pkl_migration(tmp_path):
    df = DataFrameBuilder().add_column("a", [1, 2]).add_column("b", [3, 4]).build()
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
