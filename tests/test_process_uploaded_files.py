import asyncio

from tests.utils.builders import DataFrameBuilder, UploadFileBuilder

from services.upload import UploadProcessingService
from upload_core import UploadCore
from utils.upload_store import UploadedDataStore
from services.device_learning_service import DeviceLearningService


def test_multi_part_upload_row_count():
    df = (
        DataFrameBuilder()
        .add_column("A", [1, 2, 3, 4])
        .add_column("B", ["a", "b", "c", "d"])
        .build()
    )
    b64 = UploadFileBuilder().with_dataframe(df).as_base64().split(",", 1)[1]
    prefix = "data:text/csv;base64,"
    mid = len(b64) // 2
    part1 = prefix + b64[:mid]
    part2 = prefix + b64[mid:]

    store = UploadedDataStore()
    learning = DeviceLearningService()
    processing = UploadProcessingService(store, learning)
    cb = UploadCore(processing, learning, store)
    # ensure validator attribute is initialized
    ok, msg = cb.validator.validate("sample.csv", part1)
    assert ok, msg
    res = asyncio.run(
        cb.process_uploaded_files([part1, part2], ["sample.csv", "sample.csv"])
    )
    info = res[2]
    assert info["sample.csv"]["rows"] == len(df)
    stored = store.get_all_data()["sample.csv"]
    assert len(stored) == len(df)
