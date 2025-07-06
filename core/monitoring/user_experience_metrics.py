from __future__ import annotations

"""User experience metrics and alerting utilities."""

import logging
import smtplib
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class AlertConfig:
    slack_webhook: Optional[str] = None
    email: Optional[str] = None
    webhook_url: Optional[str] = None


class AlertDispatcher:
    """Send alerts to Slack, email or a generic webhook."""

    def __init__(self, config: AlertConfig) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)

    def send_alert(self, message: str) -> None:
        """Dispatch alert message via configured channels."""
        if self.config.slack_webhook:
            try:
                requests.post(
                    self.config.slack_webhook,
                    json={"text": message},
                    timeout=5,
                )
            except Exception as exc:  # pragma: no cover - network
                self.logger.warning("Slack alert failed: %s", exc)

        if self.config.webhook_url:
            try:
                requests.post(
                    self.config.webhook_url,
                    json={"message": message},
                    timeout=5,
                )
            except Exception as exc:  # pragma: no cover - network
                self.logger.warning("Webhook alert failed: %s", exc)

        if self.config.email:
            try:
                smtp = smtplib.SMTP("localhost")
                smtp.sendmail("noreply@example.com", [self.config.email], message)
                smtp.quit()
            except Exception as exc:  # pragma: no cover - external
                self.logger.warning("Email alert failed: %s", exc)
