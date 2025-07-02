import pandas as pd
import pytest

from utils.upload_store import UploadedDataStore


def test_unsafe_filenames_rejected(tmp_path):
    store = UploadedDataStore(storage_dir=tmp_path)
    df = pd.DataFrame({"a": [1]})

    with pytest.raises(ValueError):
        store.add_file("../bad.csv", df)

    with pytest.raises(ValueError):
        store.add_file("..\\bad.csv", df)

    with pytest.raises(ValueError):
        store.add_file("bad\\name.csv", df)
