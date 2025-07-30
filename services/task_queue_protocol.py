"""Protocol specification for asynchronous task queues."""

from typing import Any, Awaitable, Callable, Dict, Protocol, runtime_checkable


@runtime_checkable
class TaskQueueProtocol(Protocol):
    """Protocol for async task management."""

    def create_task(
        self,
        func: Callable[[Callable[[int], None]], Awaitable[Any]] | Awaitable[Any],
    ) -> str: ...

    def get_status(self, task_id: str) -> Dict[str, Any]: ...

    def clear_task(self, task_id: str) -> None: ...


__all__ = ["TaskQueueProtocol"]
