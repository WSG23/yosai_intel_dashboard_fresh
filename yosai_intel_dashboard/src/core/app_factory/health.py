from __future__ import annotations

from typing import Any

from yosai_intel_dashboard.src.core.secret_manager import validate_secrets
from factories import health_check as db_health_check


def check_critical_dependencies() -> tuple[bool, str | None]:
    """Verify critical services like the database and secrets store.

    Returns a tuple ``(healthy, reason)`` where ``healthy`` indicates if all
    dependencies are functioning.  When ``healthy`` is ``False`` the ``reason``
    contains a human readable explanation.
    """

    try:
        db_status = db_health_check()
        if not db_status.healthy:
            return False, f"database unhealthy: {db_status.details}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"database check failed: {exc}"

    try:
        secrets = validate_secrets()
        if not secrets.get("valid", False):
            missing = ", ".join(secrets.get("missing", []))
            details = f"missing secrets: {missing}" if missing else "secret validation failed"
            return False, details
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"secret validation failed: {exc}"

    return True, None


def register_health_endpoints(server: Any, progress_events: Any | None = None) -> None:
    """Register common health check endpoints."""

    @server.route("/health", methods=["GET"])
    def health():
        """Aggregate health check for critical dependencies."""
        healthy, reason = check_critical_dependencies()
        if healthy:
            return {"status": "healthy"}, 200
        return {"status": "unhealthy", "reason": reason}, 503

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


__all__ = ["register_health_endpoints", "check_critical_dependencies"]
