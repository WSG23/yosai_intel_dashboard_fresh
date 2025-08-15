import types
from unittest.mock import AsyncMock

import pytest

from yosai_intel_dashboard.src.services.analytics.async_repository import AsyncEventRepository


class DummySession:
    def __init__(self):
        self.added = []
        self.executed = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def begin(self):
        return self

    async def add(self, obj):
        self.added.append(obj)

    async def add_all(self, objs):
        self.added.extend(objs)

    async def execute(self, stmt):
        self.executed.append(stmt)
        return types.SimpleNamespace(
            rowcount=1, scalars=lambda: types.SimpleNamespace(all=lambda: [])
        )


@pytest.mark.asyncio
async def test_bulk_insert_no_events():
    factory = AsyncMock()
    repo = AsyncEventRepository(session_factory=factory)
    await repo.bulk_insert_events([])
    factory.assert_not_called()


@pytest.mark.asyncio
async def test_update_and_delete():
    sess = DummySession()
    factory = AsyncMock(return_value=sess)
    repo = AsyncEventRepository(session_factory=factory)
    rc = await repo.update_event("e1", status="ok")
    assert rc == 1
    rc = await repo.delete_event("e1")
    assert rc == 1
    assert len(sess.executed) == 2
