import asyncio

from yosai_intel_dashboard.src.services.progress_events import ProgressEventManager
from yosai_intel_dashboard.src.services.task_queue import clear_task, create_task


def test_progress_event_generator():
    manager = ProgressEventManager(interval=0.01)

    async def sample():
        await asyncio.sleep(0.02)
        return "ok"

    tid = create_task(sample())
    events = list(manager.generator(tid))
    clear_task(tid)
    assert events[0] == "data: 0\n\n"
    assert events[-1] == "data: 100\n\n"
