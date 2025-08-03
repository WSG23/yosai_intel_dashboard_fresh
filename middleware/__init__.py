from importlib import import_module
from typing import Any

__all__ = [
    "TimingMiddleware",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
]


def __getattr__(name: str) -> Any:
    if name == "TimingMiddleware":
        return import_module("middleware.performance").TimingMiddleware
    if name == "RateLimitMiddleware":
        return import_module("middleware.rate_limit").RateLimitMiddleware
    if name == "SecurityHeadersMiddleware":
        return import_module("middleware.security_headers").SecurityHeadersMiddleware
    raise AttributeError(name)
