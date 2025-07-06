import asyncio
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "upload_queue_manager",
    str(
        Path(__file__).resolve().parents[1] / "services/upload/upload_queue_manager.py"
    ),
)
_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(_mod)
UploadQueueManager = _mod.UploadQueueManager


async def _handler(item: str) -> str:
    await asyncio.sleep(0)
    return item


def _drain(manager: UploadQueueManager):
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

    return asyncio.run(_run())


def test_priority_order():
    state = {}
    q = UploadQueueManager(state, max_concurrent=1)
    q.add_files(["low"], priority=5)
    q.add_files(["high"], priority=0)
    results = _drain(q)
    assert results == ["high", "low"]


def test_persistence_roundtrip():
    state = {}
    q1 = UploadQueueManager(state)
    q1.add_files(["a", "b"], priority=1)
    q2 = UploadQueueManager(state)
    status = q2.get_queue_status()
    assert status["pending"] == 2
