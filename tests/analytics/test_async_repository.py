import types
from unittest.mock import AsyncMock

import importlib.util
import pathlib
import pytest

spec = importlib.util.spec_from_file_location(
    "async_repository",
    pathlib.Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard"
    / "src"
    / "services"
    / "analytics"
    / "async_repository.py",
)
repo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repo)  # type: ignore[arg-type]
AsyncEventRepository = repo.AsyncEventRepository


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
    repository = AsyncEventRepository(session_factory=factory)
    await repository.bulk_insert_events([])
    factory.assert_not_called()


@pytest.mark.asyncio
async def test_update_and_delete():
    sess = DummySession()
    factory = AsyncMock(return_value=sess)
    repository = AsyncEventRepository(session_factory=factory)
    rc = await repository.update_event("e1", status="ok")
    assert rc == 1
    rc = await repository.delete_event("e1")
    assert rc == 1
    assert len(sess.executed) == 2


@pytest.mark.asyncio
async def test_shutdown_disposes_engine(monkeypatch):
    dispose = AsyncMock()
    monkeypatch.setattr(repo, "engine", types.SimpleNamespace(dispose=dispose))
    await repo.shutdown()
    dispose.assert_awaited_once()
