from __future__ import annotations

"""Wrapper around Alembic commands for managing schema migrations.

The :class:`MigrationManager` simplifies common upgrade and downgrade
operations and keeps a small in-memory history for rollbacks.
"""

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

    def upgrade(self, revision: str = "head", *, dry_run: bool = False) -> None:
        """Upgrade to ``revision``. If ``dry_run`` is True, emit SQL only."""
        if dry_run:
            target = "heads" if revision == "head" else revision
            command.upgrade(self.config, target, sql=True)
            logger.info("Dry-run upgrade to %s", target)
            return

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
