"""Simple notification service dispatching alerts via configured channels."""

from __future__ import annotations

from typing import Any, Dict, Optional



class NotificationService:
    """Dispatch messages to Slack, email or a generic webhook."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        from yosai_intel_dashboard.src.core.monitoring.user_experience_metrics import (
            AlertConfig,
            AlertDispatcher,
        )

        if config is None:
            from yosai_intel_dashboard.src.infrastructure.config import (
                get_monitoring_config,
            )

            cfg = get_monitoring_config()
            if isinstance(cfg, dict):
                alert_cfg = cfg.get("alerting", {})
            else:
                alert_cfg = getattr(cfg, "alerting", {})
                if hasattr(alert_cfg, "model_dump"):
                    alert_cfg = alert_cfg.model_dump()
        else:
            alert_cfg = config

        self._dispatcher = AlertDispatcher(
            AlertConfig(
                slack_webhook=alert_cfg.get("slack_webhook"),
                email=alert_cfg.get("email"),
                webhook_url=alert_cfg.get("webhook_url"),
            )
        )

    # ------------------------------------------------------------------
    def send(self, message: str) -> None:
        """Send an alert message through configured channels."""
        self._dispatcher.send_alert(message)


__all__ = ["NotificationService"]
