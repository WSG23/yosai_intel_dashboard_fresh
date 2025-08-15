import asyncio

from yosai_intel_dashboard.src.services.upload.upload_queue_manager import UploadQueueManager


async def _handler(item: str) -> str:
    await asyncio.sleep(0)
    return item


def _drain(manager: UploadQueueManager, run):
    async def _run():
        results = []
        while True:
            done = await manager.process_queue(_handler)
            if done:
                results.extend(res for _, res in done)
            status = manager.get_queue_status()
            if status["pending"] == 0 and status["active"] == 0:
                break
            await asyncio.sleep(0)
        return results

    return run(_run())


def test_priority_order(async_runner):
    state = {}
    q = UploadQueueManager(state, max_concurrent=1)
    q.add_files(["low"], priority=5)
    q.add_files(["high"], priority=0)
    results = _drain(q, async_runner)
    assert results == ["high", "low"]


def test_persistence_roundtrip(async_runner):
    state = {}
    q1 = UploadQueueManager(state)
    q1.add_files(["a", "b"], priority=1)
    q2 = UploadQueueManager(state)
    status = q2.get_queue_status()
    assert status["pending"] == 2
