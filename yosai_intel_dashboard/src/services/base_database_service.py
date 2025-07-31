from __future__ import annotations

import logging
from typing import Any, Optional

from core.base_model import BaseModel


class BaseDatabaseService(BaseModel):
    """Base service providing optional database and logging support."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
