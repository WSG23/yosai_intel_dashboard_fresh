import json

import asyncio
from starlette.requests import Request
from starlette.responses import Response

from src.middleware.validation import ValidationMiddleware
from pydantic import BaseModel


class QueryModel(BaseModel):
    q: int


class BodyModel(BaseModel):
    name: str


def test_invalid_body():
    middleware = ValidationMiddleware(lambda req: Response(), body_model=BodyModel)

    async def _run():
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/",
            "query_string": b"",
            "headers": [(b"content-type", b"application/json")],
            "client": ("test", 0),
        }

        async def receive():
            return {"type": "http.request", "body": json.dumps({"name": 123}).encode()}

        request = Request(scope, receive)
        response = await middleware.dispatch(request, lambda req: Response())
        return response.status_code

    assert asyncio.run(_run()) == 422


def test_invalid_query():
    middleware = ValidationMiddleware(lambda req: Response(), query_model=QueryModel)

    async def _run():
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"q=abc",
            "headers": [],
            "client": ("test", 0),
        }

        async def receive():
            return {"type": "http.request", "body": b""}

        request = Request(scope, receive)
        response = await middleware.dispatch(request, lambda req: Response())
        return response.status_code

    assert asyncio.run(_run()) == 422

