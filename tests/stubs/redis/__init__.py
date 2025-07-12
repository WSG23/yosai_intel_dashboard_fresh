class FakeRedis:
    async def get(self, key):
        return None


class asyncio:
    Redis = FakeRedis
