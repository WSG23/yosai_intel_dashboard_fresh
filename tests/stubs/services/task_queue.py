from typing import Any, Awaitable, Callable, Dict

from yosai_intel_dashboard.src.services.task_queue_protocol import TaskQueueProtocol


class StubTaskQueue(TaskQueueProtocol):
    def __init__(self) -> None:
        self.created = []

    def create_task(
        self, func: Callable[[Callable[[int], None]], Awaitable[Any]] | Awaitable[Any]
    ) -> str:
        if hasattr(func, "close"):
            func.close()
        tid = f"tid{len(self.created)}"
        self.created.append(tid)
        return tid

    def get_status(self, task_id: str) -> Dict[str, Any]:
        return {"progress": 0}

    def clear_task(self, task_id: str) -> None:
        pass


__all__ = ["StubTaskQueue"]
