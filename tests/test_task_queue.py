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


def test_task_queue_progress():
    async def sample(progress):
        for i in range(5):
            await asyncio.sleep(0.01)
            progress((i + 1) * 20)
        return "ok"

    tid = create_task(sample)
    last = 0
    for _ in range(200):
        status = get_status(tid)
        assert status["progress"] >= last
        last = status["progress"]
        if status.get("done"):
            break
        time.sleep(0.01)
    status = get_status(tid)
    assert status.get("done") is True
    assert status.get("result") == "ok"
    assert status["progress"] == 100
    clear_task(tid)
