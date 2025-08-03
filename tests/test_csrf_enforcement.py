import asyncio
from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from starlette.responses import Response
from itsdangerous import BadSignature, URLSafeTimedSerializer
import pytest

serializer = URLSafeTimedSerializer("secret")
app = FastAPI()


@app.middleware("http")
async def enforce(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS", "TRACE"}:
        token = request.headers.get("X-CSRFToken")
        if not token:
            raise HTTPException(status_code=400, detail="Missing CSRF token")
        try:
            serializer.loads(token, max_age=3600)
        except BadSignature:
            raise HTTPException(status_code=400, detail="Invalid CSRF token")
    return await call_next(request)


def _build_request(method="POST", headers=None):
    scope = {
        "type": "http",
        "method": method,
        "path": "/submit",
        "query_string": b"",
        "headers": headers or [],
        "client": ("test", 0),
    }

    async def receive():
        return {"type": "http.request", "body": b""}

    return Request(scope, receive)


def test_csrf_missing_token():
    req = _build_request()

    async def call_next(_):
        return Response("ok")

    with pytest.raises(HTTPException):
        asyncio.run(enforce(req, call_next))


def test_csrf_with_token():
    token = serializer.dumps("csrf")
    headers = [(b"x-csrftoken", token.encode())]
    req = _build_request(headers=headers)

    async def call_next(_):
        return Response("ok")

    resp = asyncio.run(enforce(req, call_next))
    assert resp.status_code == 200
