import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from services.task_queue import clear_task, create_task, get_status


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


def test_task_queue_thread_safety():
    async def sample(progress):
        for i in range(3):
            await asyncio.sleep(0.01)
            progress((i + 1) * 33)
        return "ok"

    def worker(_: int) -> str:
        tid = create_task(sample)
        while True:
            status = get_status(tid)
            if status.get("done"):
                break
            time.sleep(0.01)
        result = status.get("result")
        clear_task(tid)
        return result

    with ThreadPoolExecutor(max_workers=5) as exc:
        results = list(exc.map(worker, range(10)))

    assert all(res == "ok" for res in results)

    from services import task_queue

    assert task_queue._tasks == {}
