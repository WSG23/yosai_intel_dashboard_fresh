import base64
import asyncio
import pandas as pd

from services.data_processing.async_file_processor import AsyncFileProcessor
from services.progress_event_manager import progress_manager
from services.upload.processing import UploadProcessingService
from utils.upload_store import UploadedDataStore


def _encode_df(df: pd.DataFrame) -> str:
    data = df.to_csv(index=False).encode("utf-8", "surrogatepass")
    b64 = base64.b64encode(data).decode()
    return f"data:text/csv;base64,{b64}"


def test_async_processor_progress_and_surrogates():
    df = pd.DataFrame({"col": ["A\ud83d", "B"]})
    content = _encode_df(df)
    prog: list[int] = []
    proc = AsyncFileProcessor(chunk_size=5)
    out = asyncio.run(
        proc.process_file(content, "t.csv", lambda f, p: prog.append(p))
    )
    assert prog and prog[-1] == 100
    assert "\ud83d" not in out["col"].iloc[0]


def test_upload_processing_async(tmp_path):
    df = pd.DataFrame({"x": ["A\ud83d"], "y": [1]})
    content = _encode_df(df)
    store = UploadedDataStore(storage_dir=tmp_path)
    service = UploadProcessingService(store)

    progress: list[int] = []
    cb = lambda f, p: progress.append(p)
    progress_manager.register(cb)
    try:
        res = asyncio.run(service.process_files([content], ["data.csv"]))
    finally:
        progress_manager.unregister(cb)

    assert progress and progress[-1] == 100
    info = res[2]
    assert info["data.csv"]["rows"] == 1
    stored = store.get_all_data()["data.csv"]
    assert "\ud83d" not in str(stored.iloc[0, 0])

