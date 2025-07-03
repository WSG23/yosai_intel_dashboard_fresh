"""Basic attack detection utilities."""

import logging


class AttackDetection:
    """Log detected attacks"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def record(self, message: str) -> None:
        self.logger.warning("Security alert: %s", message)
