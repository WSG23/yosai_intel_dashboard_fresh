from __future__ import annotations

"""Middleware sanitizing request data using :class:`UnicodeHandler`."""

import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from yosai_intel_dashboard.src.utils.unicode_handler import UnicodeHandler

logger = logging.getLogger(__name__)


class UnicodeSanitizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.query_params:
            sanitized = {
                k: UnicodeHandler.sanitize(v) for k, v in request.query_params.items()
            }
            request._query_params = request.query_params.__class__(sanitized)
            logger.debug("Sanitized query for %s", request.url.path)

        if request.method in {"POST", "PUT", "PATCH"}:
            body = await request.body()
            try:
                text = body.decode("utf-8")
            except Exception:
                text = ""
            cleaned = UnicodeHandler.sanitize(text)
            request._body = cleaned.encode("utf-8")
            logger.debug("Sanitized body for %s", request.url.path)

        response = await call_next(request)
        return response


__all__ = ["UnicodeSanitizationMiddleware"]
