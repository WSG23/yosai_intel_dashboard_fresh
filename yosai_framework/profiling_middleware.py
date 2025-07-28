import time
from typing import Callable, Awaitable

import psutil
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class ProfilingMiddleware(BaseHTTPMiddleware):
    """Record request latency and memory usage to Prometheus metrics."""

    def __init__(self, app, service) -> None:
        super().__init__(app)
        self.service = service
        self.proc = psutil.Process()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.perf_counter()
        start_mem = self.proc.memory_info().rss / (1024 * 1024)
        try:
            response = await call_next(request)
            return response
        finally:
            duration = time.perf_counter() - start_time
            end_mem = self.proc.memory_info().rss / (1024 * 1024)
            mem_delta = max(end_mem - start_mem, 0)
            if hasattr(self.service, "request_total"):
                self.service.request_total.inc()
            if hasattr(self.service, "request_duration"):
                self.service.request_duration.observe(duration)
            if hasattr(self.service, "request_memory"):
                self.service.request_memory.observe(mem_delta)
