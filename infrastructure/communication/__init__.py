"""Unified service communication primitives."""

from .protocols import MessageBus, ServiceClient
from .rest_client import AsyncRestClient, RetryPolicy, create_service_client, CircuitBreakerOpen
from .message_queue import AsyncQueueClient
from .circuit_breaker import CircuitBreaker

__all__ = [
    "MessageBus",
    "ServiceClient",
    "AsyncRestClient",
    "AsyncQueueClient",
    "RetryPolicy",
    "create_service_client",
    "CircuitBreaker",
    "CircuitBreakerOpen",
]
