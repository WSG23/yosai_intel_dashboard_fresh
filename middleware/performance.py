import time
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from yosai_intel_dashboard.src.infrastructure.monitoring.performance_profiler import (
    PerformanceProfiler,
)
from yosai_intel_dashboard.src.infrastructure.monitoring.request_metrics import (
    request_duration,
)


class TimingMiddleware(BaseHTTPMiddleware):
    """Measure request processing time and update profiling metrics."""

    def __init__(self, app):
        super().__init__(app)
        self.profiler = PerformanceProfiler()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        endpoint = request.url.path
        start = time.perf_counter()
        try:
            with self.profiler.profile_endpoint(endpoint):
                response = await call_next(request)
                return response
        finally:
            elapsed = time.perf_counter() - start
            request_duration.observe(elapsed)
