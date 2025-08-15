import pytest


class FakeRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def setex(self, key, ttl, value):
        self.store[key] = value


class RBACService:
    def __init__(self, redis, ttl=60):
        self.redis = redis
        self.ttl = ttl
        self.db_calls = 0

    async def _fetch_roles(self, user_id):
        self.db_calls += 1
        return ["admin"]

    async def get_roles(self, user_id):
        cached = await self.redis.get(f"roles:{user_id}")
        if cached:
            return cached
        roles = await self._fetch_roles(user_id)
        await self.redis.setex(f"roles:{user_id}", self.ttl, roles)
        return roles


@pytest.mark.asyncio
async def test_service_uses_cache():
    redis = FakeRedis()
    svc = RBACService(redis)

    roles1 = await svc.get_roles("u1")
    assert roles1 == ["admin"]
    assert svc.db_calls == 1

    roles2 = await svc.get_roles("u1")
    assert roles2 == ["admin"]
    assert svc.db_calls == 1  # cached
