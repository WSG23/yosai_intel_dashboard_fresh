import asyncio
from infrastructure.communication import AsyncRestClient, AsyncQueueClient

class DummyRequest:
    async def __aenter__(self):
        return DummyResponse()

    async def __aexit__(self, exc_type, exc, tb):
        pass

class DummyResponse:
    status = 200
    headers = {"Content-Type": "application/json"}
    async def json(self):
        return {"ok": True}
    async def text(self):
        return "{}"
    def raise_for_status(self):
        pass

class DummySession:
    def request(self, *args, **kwargs):
        return DummyRequest()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

def test_rest_client_request(monkeypatch):
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession())
    client = AsyncRestClient("http://service")
    result = asyncio.run(client.request("GET", "/ping"))
    assert result == {"ok": True}

def test_queue_publish_consume():
    q = AsyncQueueClient()
    result = []
    async def handler(msg):
        result.append(msg)
    async def run_all():
        consumer = asyncio.create_task(q.subscribe("t", handler))
        await q.publish("t", 1)
        await asyncio.sleep(0.05)
        consumer.cancel()
    asyncio.run(run_all())
    assert result == [1]
