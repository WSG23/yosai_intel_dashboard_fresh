import pytest

from tests.utils.builders import DataFrameBuilder
from yosai_intel_dashboard.src.utils.upload_store import UploadedDataStore


def test_unsafe_filenames_rejected(tmp_path):
    store = UploadedDataStore(storage_dir=tmp_path)
    df = DataFrameBuilder().add_column("a", [1]).build()

    with pytest.raises(ValueError):
        store.add_file("../bad.csv", df)

    with pytest.raises(ValueError):
        store.add_file("..\\bad.csv", df)

    with pytest.raises(ValueError):
        store.add_file("bad\\name.csv", df)
