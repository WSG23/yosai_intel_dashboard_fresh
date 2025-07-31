from __future__ import annotations

import time
from typing import Iterator

from flask import Response, stream_with_context

from yosai_intel_dashboard.src.services.task_queue import get_status


class ProgressEventManager:
    """Simple manager streaming task progress via Server-Sent Events."""

    def __init__(self, interval: float = 0.016) -> None:
        self.interval = interval

    def generator(self, task_id: str) -> Iterator[str]:
        """Yield SSE formatted progress updates for ``task_id`` until completion."""
        while True:
            status = get_status(task_id)
            progress = int(status.get("progress", 0))
            yield f"data: {progress}\n\n"
            if status.get("done"):
                break
            # This generator runs synchronously inside a request handler, so
            # a simple blocking sleep avoids the overhead of spawning an event
            # loop for each iteration.
            time.sleep(self.interval)

    def stream(self, task_id: str) -> Response:
        """Return an SSE ``Response`` streaming progress for ``task_id``."""
        return Response(
            stream_with_context(self.generator(task_id)),
            mimetype="text/event-stream",
        )


__all__ = ["ProgressEventManager"]
