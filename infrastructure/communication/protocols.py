from __future__ import annotations

from typing import Any, Awaitable, Callable, Protocol


class MessageBus(Protocol):
    """Asynchronous message bus protocol."""

    async def publish(self, topic: str, message: Any) -> None:
        """Publish *message* to *topic*."""
        ...

    async def subscribe(
        self, topic: str, handler: Callable[[Any], Awaitable[None]]
    ) -> None:
        """Invoke *handler* for each message from *topic*."""
        ...


class ServiceClient(Protocol):
    """Protocol for asynchronous service clients."""

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Execute an HTTP request and return the decoded response."""
        ...

