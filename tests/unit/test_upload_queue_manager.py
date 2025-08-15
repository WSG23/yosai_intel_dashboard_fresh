import asyncio

from yosai_intel_dashboard.src.services.upload.upload_queue_manager import UploadQueueManager


async def _dummy_handler(item):
    await asyncio.sleep(0.01)
    return item * 2


def test_add_and_status():
    state = {}
    q = UploadQueueManager(state, max_concurrent=2)
    q.add_files([1, 2, 3], priority=1)
    assert q.get_queue_status()["pending"] == 3
    assert state["queue_state"]["queue"]


def test_persistence_between_instances():
    state = {}
    q1 = UploadQueueManager(state)
    q1.add_files(["a", "b"])

    q2 = UploadQueueManager(state)
    status = q2.get_queue_status()
    assert status["pending"] == 2


def test_process_queue_executes_tasks(async_runner):
    async def _run():
        q = UploadQueueManager(max_concurrent=2)
        q.add_files([1, 2, 3])

        results = []
        for _ in range(10):
            results.extend(await q.process_queue(_dummy_handler))
            if (
                not q.get_queue_status()["pending"]
                and not q.get_queue_status()["active"]
            ):
                break
            await asyncio.sleep(0.02)
        processed = [r for _, r in results]
        return processed

    processed = async_runner(_run())
    assert sorted(processed) == [2, 4, 6]
