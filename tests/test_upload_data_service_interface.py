import pandas as pd

from yosai_intel_dashboard.src.services.upload_data_service import (
    UploadDataService,
    clear_uploaded_data,
    get_file_info,
    get_uploaded_data,
    get_uploaded_filenames,
    load_dataframe,
)
from utils.upload_store import UploadedDataStore


def test_service_helpers(tmp_path):
    store = UploadedDataStore(storage_dir=tmp_path)
    service = UploadDataService(store)

    df = pd.DataFrame({"a": [1, 2]})
    store.add_file("a.csv", df)

    assert get_uploaded_filenames(service) == ["a.csv"]
    data = get_uploaded_data(service)
    assert list(data.keys()) == ["a.csv"]
    assert load_dataframe("a.csv", service).equals(df)

    info = get_file_info(service)
    assert info["a.csv"]["rows"] == 2

    clear_uploaded_data(service)
    assert get_uploaded_filenames(service) == []
