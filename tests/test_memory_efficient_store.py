import pandas as pd
from utils.upload_store import UploadedDataStore


def test_memory_cleanup_after_save(tmp_path):
    store = UploadedDataStore(storage_dir=tmp_path)
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    store.add_file("sample.csv", df)
    store.wait_for_pending_saves()

    assert store._data_store == {}

    info = store.get_file_info()["sample.csv"]
    assert info["rows"] == 2
    assert "path" in info

    df_loaded = store.load_dataframe("sample.csv")
    assert len(df_loaded) == 2
    # loading the dataframe should not keep it cached
    assert store._data_store == {}

    # re-load store from disk
    store2 = UploadedDataStore(storage_dir=tmp_path)
    info2 = store2.get_file_info()["sample.csv"]
    assert info2["rows"] == 2
    assert "path" in info2
