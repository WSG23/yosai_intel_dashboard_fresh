from __future__ import annotations

from typing import Any

from yosai_intel_dashboard.src.core.secret_manager import validate_secrets
from factories import health_check as db_health_check


def register_health_endpoints(server: Any, progress_events: Any | None = None) -> None:
    """Register common health check endpoints."""

    @server.route("/health", methods=["GET"])
    def health():
        """Basic health check."""
        return {"status": "ok"}, 200

    @server.route("/health/db", methods=["GET"])
    def health_db():
        """Database connectivity check."""
        status = db_health_check()
        return status.model_dump(), 200

    @server.route("/health/secrets", methods=["GET"])
    def health_secrets():
        """Return validation summary for required secrets."""
        return validate_secrets(), 200

    if progress_events is not None:

        @server.route("/upload/progress/<task_id>")
        def upload_progress(task_id: str):
            """Stream task progress updates as Server-Sent Events."""
            return progress_events.stream(task_id)


__all__ = ["register_health_endpoints"]
