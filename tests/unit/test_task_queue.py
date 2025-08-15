from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from yosai_intel_dashboard.src.services.task_queue import TaskQueue

queue = TaskQueue()
import pytest


def test_task_queue_basic():
    async def sample():
        await asyncio.sleep(0.01)
        return "ok"

    tid = queue.create_task(sample)
    for _ in range(100):
        status = queue.get_status(tid)
        if status.get("done"):
            break
        time.sleep(0.01)
    status = queue.get_status(tid)
    assert status.get("done") is True
    assert status.get("result") == "ok"
    queue.clear_task(tid)


def test_task_queue_progress():
    async def sample(progress):
        for i in range(5):
            await asyncio.sleep(0.01)
            progress((i + 1) * 20)
        return "ok"

    tid = queue.create_task(sample)
    last = 0
    for _ in range(200):
        status = queue.get_status(tid)
        assert status["progress"] >= last
        last = status["progress"]
        if status.get("done"):
            break
        time.sleep(0.01)
    status = queue.get_status(tid)
    assert status.get("done") is True
    assert status.get("result") == "ok"
    assert status["progress"] == 100
    queue.clear_task(tid)


@pytest.mark.slow
def test_task_queue_thread_safety():
    async def sample(progress):
        for i in range(3):
            await asyncio.sleep(0.01)
            progress((i + 1) * 33)
        return "ok"

    def worker(_: int) -> str:
        tid = queue.create_task(sample)
        while True:
            status = queue.get_status(tid)
            if status.get("done"):
                break
            time.sleep(0.01)
        result = status.get("result")
        queue.clear_task(tid)
        return result

    with ThreadPoolExecutor(max_workers=5) as exc:
        results = list(exc.map(worker, range(10)))

    assert all(res == "ok" for res in results)

    assert queue._tasks == {}


def test_task_queue_idempotency():
    q = TaskQueue()

    async def sample():
        await asyncio.sleep(0.01)
        return "ok"

    tid1 = q.create_task(sample, idempotency_key="same")
    tid2 = q.create_task(sample, idempotency_key="same")
    assert tid1 == tid2
    for _ in range(100):
        status = q.get_status(tid1)
        if status.get("done"):
            break
        time.sleep(0.01)
    assert q.get_status(tid1)["result"] == "ok"
    q.clear_task(tid1)


def test_task_queue_workers():
    q = TaskQueue(workers=2)

    async def sample():
        await asyncio.sleep(0.1)
        return "ok"

    start = time.perf_counter()
    tids = [q.create_task(sample) for _ in range(2)]
    for tid in tids:
        while True:
            status = q.get_status(tid)
            if status.get("done"):
                break
            time.sleep(0.01)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.19
    for tid in tids:
        q.clear_task(tid)
