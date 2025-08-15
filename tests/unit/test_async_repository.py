import pytest


class AsyncPersonRepository:
    def __init__(self):
        self.store = {}

    async def create(self, person):
        self.store[person["id"]] = person
        return person

    async def get_by_id(self, pid):
        return self.store.get(pid)

    async def get_all(self):
        return list(self.store.values())

    async def update(self, person):
        self.store[person["id"]] = person
        return person

    async def delete(self, pid):
        return self.store.pop(pid, None) is not None


@pytest.mark.asyncio
async def test_async_repo_crud():
    repo = AsyncPersonRepository()
    person = {"id": "1", "name": "Alice"}

    await repo.create(person)
    assert await repo.get_by_id("1") == person
    assert len(await repo.get_all()) == 1

    updated = {"id": "1", "name": "Bob"}
    await repo.update(updated)
    assert (await repo.get_by_id("1"))["name"] == "Bob"

    assert await repo.delete("1") is True
    assert await repo.get_by_id("1") is None
