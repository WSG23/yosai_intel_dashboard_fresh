import asyncio
from services.progress_events import ProgressEventManager
from services.task_queue import create_task, clear_task


def test_progress_event_generator():
    manager = ProgressEventManager(interval=0.01)

    async def sample():
        await asyncio.sleep(0.02)
        return "ok"

    tid = create_task(sample())
    events = list(manager.generator(tid))
    clear_task(tid)
    assert events[0] == "0"
    assert events[-1] == "100"
