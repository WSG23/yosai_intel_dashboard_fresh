import logging
from typing import Any, Optional


class BaseModel:
    __slots__ = ("config", "logger", "db")

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.db = db


__all__ = ["BaseModel"]
