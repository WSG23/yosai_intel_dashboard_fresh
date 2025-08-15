import types

import httpx
import pytest

pytestmark = pytest.mark.anyio

from middleware.security_headers import SecurityHeadersMiddleware


@pytest.fixture
def anyio_backend():
    return "asyncio"


def create_app():
    from fastapi import FastAPI

    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    def _root():
        return {"ok": True}

    return app


async def test_security_headers_present():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.headers["Content-Security-Policy"] == "default-src 'self'"
    assert resp.headers["Strict-Transport-Security"]
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert (
        resp.headers["Permissions-Policy"]
        == "geolocation=(), camera=(), microphone=(), fullscreen=()"
    )
