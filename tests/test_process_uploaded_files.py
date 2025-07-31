import asyncio

from services.device_learning_service import DeviceLearningService
from services.upload import UploadProcessingService
from services.upload.upload_core import UploadCore
from tests.fakes import FakeUploadDataService
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder
from yosai_intel_dashboard.src.utils.upload_store import UploadedDataStore


def test_multi_part_upload_row_count(async_runner):
    df = pd.DataFrame(
        {
            "A": [1, 2, 3, 4],
            "B": ["a", "b", "c", "d"],
        }
    )
    b64 = UploadFileBuilder().with_dataframe(df).as_base64().split(",", 1)[1]
    prefix = "data:text/csv;base64,"
    mid = len(b64) // 2
    part1 = prefix + b64[:mid]
    part2 = prefix + b64[mid:]

    store = UploadedDataStore()
    learning = DeviceLearningService()
    data_svc = FakeUploadDataService(store)
    processing = UploadProcessingService(store, learning, data_svc)
    cb = UploadCore(processing, learning, store)
    # ensure validator attribute is initialized
    ok, msg = cb.validator.validate("sample.csv", part1)
    assert ok, msg
    res = async_runner(
        cb.process_uploaded_files([part1, part2], ["sample.csv", "sample.csv"])
    )
    info = res[2]
    assert info["sample.csv"]["rows"] == len(df)
    stored = store.get_all_data()["sample.csv"]
    assert len(stored) == len(df)
