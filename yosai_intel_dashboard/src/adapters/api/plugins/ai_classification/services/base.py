from __future__ import annotations

import logging
from typing import Any


class RepositoryConfigService:
    """Base service providing repository/config storage and logging."""

    def __init__(self, repository: Any, config: Any) -> None:
        self.repository = repository
        self.config = config
        self.logger = logging.getLogger(self.__class__.__module__)


class BaseCSVProcessor(RepositoryConfigService):
    """Base class for CSV processors needing a Japanese handler."""

    def __init__(self, repository: Any, japanese_handler: Any, config: Any) -> None:
        super().__init__(repository, config)
        self.japanese_handler = japanese_handler
