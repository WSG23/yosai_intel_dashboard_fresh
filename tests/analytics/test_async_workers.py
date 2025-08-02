import asyncio
from types import SimpleNamespace

import pytest

from yosai_intel_dashboard.src.services.analytics import async_workers as workers


class StubManager:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.cleared = False

    async def start(self):
        self.started = True

    async def clear(self):
        self.cleared = True

    async def stop(self):
        self.stopped = True


@pytest.mark.asyncio
async def test_start_and_stop(monkeypatch):
    mgr = StubManager()

    async def fake_create():
        return mgr

    monkeypatch.setattr(workers, "create_advanced_cache_manager", fake_create)
    queue: asyncio.Queue[asyncio.Future] = asyncio.Queue()

    await workers.start_workers(
        calc_interval=0, cache_refresh_interval=0, task_queue=queue
    )
    await asyncio.sleep(0.1)
    await queue.put(asyncio.sleep(0))
    await asyncio.sleep(0.1)
    await workers.stop_workers()

    assert mgr.started
    assert mgr.stopped
