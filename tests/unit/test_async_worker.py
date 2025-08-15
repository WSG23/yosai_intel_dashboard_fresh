import asyncio

import pytest


class Worker:
    def __init__(self):
        self._task = None
        self.ran = False

    async def _job(self):
        self.ran = True

    async def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._job())

    async def stop(self):
        if self._task:
            await self._task
            self._task = None


@pytest.mark.asyncio
async def test_worker_schedule():
    w = Worker()
    await w.start()
    await w.stop()
    assert w.ran is True
