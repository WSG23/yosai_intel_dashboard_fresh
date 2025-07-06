from __future__ import annotations

import logging
from typing import List

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manage Alembic database migrations with simple rollback support."""

    def __init__(self, config_path: str = "alembic.ini") -> None:
        self.config = Config(config_path)
        self._history: List[str] = []

    def upgrade(self, revision: str = "head") -> None:
        command.upgrade(self.config, revision)
        self._history.append(revision)
        logger.info("Upgraded to %s", revision)

    def downgrade(self, revision: str) -> None:
        command.downgrade(self.config, revision)
        if self._history:
            self._history.pop()
        logger.info("Downgraded to %s", revision)

    def rollback(self) -> None:
        if len(self._history) < 2:
            prev = "base"
        else:
            prev = self._history[-2]
        command.downgrade(self.config, prev)
        if self._history:
            self._history.pop()
        logger.info("Rolled back to %s", prev)

    def current(self) -> None:
        command.current(self.config)


__all__ = ["MigrationManager"]
