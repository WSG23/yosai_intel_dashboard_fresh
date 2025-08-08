"""Append-only audit logger for security events with SIEM streaming."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from yosai_intel_dashboard.src.core.integrations.siem_connectors import send_to_siem
from yosai_intel_dashboard.src.infrastructure.monitoring.alerts import AlertManager
from yosai_intel_dashboard.src.infrastructure.monitoring.anomaly_detector import (
    AnomalyDetector,
)


@dataclass(frozen=True)
class AuditEvent:
    """Represents a security event captured by the audit logger."""

    type: str
    timestamp: str
    details: Dict[str, Any]


class SecurityAuditLogger:
    """Append-only logger that streams events to SIEM and triggers alerts."""

    def __init__(
        self,
        log_path: str | Path = "security_audit.log",
        *,
        siem_system: str = "elk",
        alert_manager: Optional[AlertManager] = None,
        anomaly_detector: Optional[AnomalyDetector] = None,
    ) -> None:
        self.log_path = Path(log_path)
        self.siem_system = siem_system
        self.alert_manager = alert_manager or AlertManager()
        self.anomaly_detector = anomaly_detector or AnomalyDetector()

    # ------------------------------------------------------------------
    def _write_event(self, event: AuditEvent) -> None:
        """Append *event* to log file and forward to SIEM/monitoring."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event)) + "\n")

        send_to_siem(asdict(event), self.siem_system)

        user_id = event.details.get("user_id")
        source_ip = event.details.get("source_ip")
        _, is_anomaly = self.anomaly_detector.score(user_id, source_ip)
        if is_anomaly:
            # Real-time alert on anomalous event
            message = f"Anomalous security event detected: {event.details}"
            self.alert_manager._notify(message)  # pragma: no cover - alert side effect

    # ------------------------------------------------------------------
    def _create_event(self, event_type: str, details: Dict[str, Any]) -> AuditEvent:
        return AuditEvent(
            type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details,
        )

    # ------------------------------------------------------------------
    def log_auth_event(
        self,
        *,
        user_id: str,
        action: str,
        success: bool,
        source_ip: Optional[str] = None,
    ) -> None:
        """Log authentication events such as logins."""
        details = {
            "user_id": user_id,
            "action": action,
            "success": success,
            "source_ip": source_ip,
        }
        self._write_event(self._create_event("auth", details))

    # ------------------------------------------------------------------
    def log_permission_event(
        self,
        *,
        user_id: str,
        permission: str,
        granted: bool,
        resource: Optional[str] = None,
    ) -> None:
        """Log permission checks and changes."""
        details = {
            "user_id": user_id,
            "permission": permission,
            "granted": granted,
            "resource": resource,
        }
        self._write_event(self._create_event("permission", details))

    # ------------------------------------------------------------------
    def log_data_access(
        self,
        *,
        user_id: str,
        resource: str,
        action: str,
        source_ip: Optional[str] = None,
    ) -> None:
        """Log data access events."""
        details = {
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "source_ip": source_ip,
        }
        self._write_event(self._create_event("data_access", details))


__all__ = ["SecurityAuditLogger", "AuditEvent"]
