from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.body_size_limit import BodySizeLimitMiddleware


def create_app(limit: int = 10) -> FastAPI:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=limit)

    @app.post("/")
    async def root(data: dict | None = None):  # pragma: no cover - simple echo
        return {"ok": True}

    return app


def test_rejects_large_payload():
    app = create_app(limit=10)
    client = TestClient(app)
    headers = {"content-length": "11"}
    resp = client.post("/", content="x", headers=headers)
    assert resp.status_code == 413


def test_allows_small_payload():
    app = create_app(limit=10)
    client = TestClient(app)
    resp = client.post("/", json={"a": 1})
    assert resp.status_code == 200
