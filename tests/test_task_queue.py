import asyncio
import time
from services.task_queue import create_task, get_status, clear_task


def test_task_queue_basic():
    async def sample():
        await asyncio.sleep(0.01)
        return "ok"

    tid = create_task(sample)
    for _ in range(100):
        status = get_status(tid)
        if status.get("done"):
            break
        time.sleep(0.01)
    status = get_status(tid)
    assert status.get("done") is True
    assert status.get("result") == "ok"
    clear_task(tid)
