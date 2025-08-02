"""Simple logging service implementing ``LoggingProtocol``."""

from __future__ import annotations

import logging
from typing import Any

from .protocols import LoggingProtocol


class LoggingService(LoggingProtocol):
    """Basic logging wrapper around :mod:`logging`."""

    def __init__(self, level: str = "INFO") -> None:
        self._logger = logging.getLogger("yosai")
        self._level = level
        self._logger.setLevel(level)

    def log_info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(message, extra=kwargs)

    def log_warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(message, extra=kwargs)

    def log_error(
        self, message: str, error: Exception | None = None, **kwargs: Any
    ) -> None:
        if error:
            self._logger.error(message, exc_info=error, extra=kwargs)
        else:
            self._logger.error(message, extra=kwargs)

    def log_debug(self, message: str, **kwargs: Any) -> None:
        self._logger.debug(message, extra=kwargs)

    def set_log_level(self, level: str) -> None:
        self._logger.setLevel(level)
        self._level = level

    def get_log_level(self) -> str:
        return logging.getLevelName(self._logger.level)


__all__ = ["LoggingService"]
