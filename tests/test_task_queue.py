import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "task_queue", ROOT / "services" / "task_queue.py"
)
task_queue = importlib.util.module_from_spec(spec)
sys.modules["task_queue"] = task_queue
spec.loader.exec_module(task_queue)  # type: ignore
clear_task = task_queue.clear_task
create_task = task_queue.create_task
get_status = task_queue.get_status
import pytest


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


@pytest.mark.slow
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

    assert task_queue._tasks == {}
