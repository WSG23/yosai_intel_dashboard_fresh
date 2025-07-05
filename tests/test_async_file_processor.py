import asyncio
import pandas as pd
import time

from services.data_processing.async_file_processor import AsyncFileProcessor
from services.task_queue import create_task, get_status, clear_task


def test_async_file_processor_progress(tmp_path):
    df = pd.DataFrame({"a": range(5)})
    path = tmp_path / "data.csv"
    df.to_csv(path, index=False)

    processor = AsyncFileProcessor(chunk_size=2)

    async def job(progress):
        return await processor.load_csv(path, progress_callback=progress)

    tid = create_task(job)
    last = 0
    while True:
        status = get_status(tid)
        cur = status["progress"]
        assert cur >= last
        last = cur
        if status.get("done"):
            break
        time.sleep(0.01)

    result = status["result"]
    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(df)
    assert last == 100
    clear_task(tid)
