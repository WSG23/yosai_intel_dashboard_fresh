import base64
import pandas as pd

from pages import file_upload
from pages.file_upload import Callbacks
from utils.upload_store import UploadedDataStore


def _encode_df(df: pd.DataFrame) -> str:
    data = df.to_csv(index=False).encode()
    b64 = base64.b64encode(data).decode()
    return f"data:text/csv;base64,{b64}"


def test_process_uploaded_files_split(monkeypatch, tmp_path):
    # create a dataframe large enough to split
    df = pd.DataFrame({"a": range(10), "b": range(10)})
    df1 = df.iloc[:5]
    df2 = df.iloc[5:]

    contents_list = [_encode_df(df1), _encode_df(df2)]
    filenames_list = ["big.csv", "big.csv"]

    store = UploadedDataStore(storage_dir=tmp_path)
    monkeypatch.setattr(file_upload, "_uploaded_data_store", store)

    cb = Callbacks()
    result = cb.process_uploaded_files(contents_list, filenames_list)
    info = result[2]

    assert info["big.csv"]["rows"] == len(df)
    assert list(store.get_filenames()) == ["big.csv"]

