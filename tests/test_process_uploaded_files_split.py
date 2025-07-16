import asyncio

from tests.utils.builders import DataFrameBuilder, UploadFileBuilder

from pages import file_upload
from services.upload import UploadProcessingService
from upload_core import UploadCore
from utils.upload_store import UploadedDataStore
from services.device_learning_service import DeviceLearningService
from tests.fakes import FakeUploadDataService


def _encode_df(df: pd.DataFrame) -> str:
    return UploadFileBuilder().with_dataframe(df).as_base64()


def test_process_uploaded_files_split(monkeypatch, tmp_path, async_runner):
    # create a dataframe large enough to split
    df = (
        DataFrameBuilder().add_column("a", range(10)).add_column("b", range(10)).build()
    )
    df1 = df.iloc[:5]
    df2 = df.iloc[5:]

    contents_list = [_encode_df(df1), _encode_df(df2)]
    filenames_list = ["big.csv", "big.csv"]

    store = UploadedDataStore(storage_dir=tmp_path)
    monkeypatch.setattr(file_upload, "_uploaded_data_store", store)

    learning = DeviceLearningService()
    data_svc = FakeUploadDataService(store)
    processing = UploadProcessingService(store, learning, data_svc)
    cb = UploadCore(processing, learning, store)
    ok, msg = cb.validator.validate("big.csv", contents_list[0])
    assert ok, msg
    result = async_runner(cb.process_uploaded_files(contents_list, filenames_list))
    info = result[2]

    assert info["big.csv"]["rows"] == len(df)
    assert list(store.get_filenames()) == ["big.csv"]
