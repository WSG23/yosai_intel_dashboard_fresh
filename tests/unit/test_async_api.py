import httpx
import pytest
from fastapi import FastAPI

app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item": item_id}


@pytest.mark.asyncio
async def test_api_endpoint():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/items/5")
        assert resp.status_code == 200
        assert resp.json() == {"item": 5}
