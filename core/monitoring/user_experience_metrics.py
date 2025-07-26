from __future__ import annotations

"""User experience metrics and alerting utilities."""

import logging
import smtplib
import asyncio
from dataclasses import dataclass
from typing import Optional

import requests

try:  # pragma: no cover - optional dependency
    import aiohttp
except Exception:  # pragma: no cover - optional dependency
    aiohttp = None

try:  # pragma: no cover - optional dependency
    import aiosmtplib
except Exception:  # pragma: no cover - optional dependency
    aiosmtplib = None


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

    # ------------------------------------------------------------------
    def _send_slack_sync(self, message: str) -> None:
        if self.config.slack_webhook:
            try:
                requests.post(
                    self.config.slack_webhook,
                    json={"text": message},
                    timeout=5,
                )
            except Exception as exc:  # pragma: no cover - network
                self.logger.warning("Slack alert failed: %s", exc)

    # ------------------------------------------------------------------
    async def _send_slack_async(self, message: str) -> None:
        if self.config.slack_webhook and aiohttp is not None:
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        self.config.slack_webhook,
                        json={"text": message},
                        timeout=aiohttp.ClientTimeout(total=5),
                    )
            except Exception as exc:  # pragma: no cover - network
                self.logger.warning("Slack alert failed: %s", exc)
        elif self.config.slack_webhook:
            self._send_slack_sync(message)

    # ------------------------------------------------------------------
    def _send_webhook_sync(self, message: str) -> None:
        if self.config.webhook_url:
            try:
                requests.post(
                    self.config.webhook_url,
                    json={"message": message},
                    timeout=5,
                )
            except Exception as exc:  # pragma: no cover - network
                self.logger.warning("Webhook alert failed: %s", exc)

    # ------------------------------------------------------------------
    async def _send_webhook_async(self, message: str) -> None:
        if self.config.webhook_url and aiohttp is not None:
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        self.config.webhook_url,
                        json={"message": message},
                        timeout=aiohttp.ClientTimeout(total=5),
                    )
            except Exception as exc:  # pragma: no cover - network
                self.logger.warning("Webhook alert failed: %s", exc)
        elif self.config.webhook_url:
            self._send_webhook_sync(message)

    # ------------------------------------------------------------------
    def _send_email_sync(self, message: str) -> None:
        if self.config.email:
            try:
                smtp = smtplib.SMTP("localhost")
                smtp.sendmail("noreply@example.com", [self.config.email], message)
                smtp.quit()
            except Exception as exc:  # pragma: no cover - external
                self.logger.warning("Email alert failed: %s", exc)

    # ------------------------------------------------------------------
    async def _send_email_async(self, message: str) -> None:
        if self.config.email and aiosmtplib is not None:
            try:
                smtp = aiosmtplib.SMTP(hostname="localhost")
                await smtp.connect()
                await smtp.sendmail(
                    "noreply@example.com",
                    [self.config.email],
                    message,
                )
                await smtp.quit()
            except Exception as exc:  # pragma: no cover - external
                self.logger.warning("Email alert failed: %s", exc)
        elif self.config.email:
            self._send_email_sync(message)

    # ------------------------------------------------------------------
    async def send_alert_async(self, message: str) -> None:
        """Asynchronously dispatch alert via configured channels."""
        await asyncio.gather(
            self._send_slack_async(message),
            self._send_webhook_async(message),
            self._send_email_async(message),
        )

    # ------------------------------------------------------------------
    def send_alert(self, message: str) -> None:
        """Dispatch alert message via configured channels."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Running inside an event loop, fall back to synchronous sending
            self._send_slack_sync(message)
            self._send_webhook_sync(message)
            self._send_email_sync(message)
        else:
            asyncio.run(self.send_alert_async(message))
