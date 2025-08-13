"""Simple logging service implementing ``LoggingProtocol`` with Unicode safety."""

from __future__ import annotations

import logging
from typing import Any, Tuple, Dict, Protocol

from unicode_toolkit import UnicodeHandler, safe_encode_text


class LoggingProtocol(Protocol):
    """Protocol describing the logging service API."""

    def log_info(self, message: str, **kwargs: Any) -> None: ...

    def log_warning(self, message: str, **kwargs: Any) -> None: ...

    def log_error(
        self, message: str, error: Exception | None = None, **kwargs: Any
    ) -> None: ...

    def log_debug(self, message: str, **kwargs: Any) -> None: ...

    def set_log_level(self, level: str) -> None: ...

    def get_log_level(self) -> str: ...


class LoggingService(LoggingProtocol):
    """Basic logging wrapper around :mod:`logging` with sanitization."""

    def __init__(self, level: str = "INFO") -> None:
        self._logger = logging.getLogger("yosai")
        self._level = level
        self._logger.setLevel(level)

    # ------------------------------------------------------------------
    def _prepare(self, message: str, kwargs: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Return sanitized ``message`` and ``kwargs``."""

        clean_msg = safe_encode_text(message)
        clean_kwargs = {k: UnicodeHandler.sanitize(v) for k, v in kwargs.items()}
        return clean_msg, clean_kwargs

    # ------------------------------------------------------------------
    def log_info(self, message: str, **kwargs: Any) -> None:
        msg, kw = self._prepare(message, kwargs)
        self._logger.info(msg, extra=kw)

    def log_warning(self, message: str, **kwargs: Any) -> None:
        msg, kw = self._prepare(message, kwargs)
        self._logger.warning(msg, extra=kw)

    def log_error(
        self, message: str, error: Exception | None = None, **kwargs: Any
    ) -> None:
        msg, kw = self._prepare(message, kwargs)
        if error:
            kw["error"] = safe_encode_text(str(error))
            self._logger.error(msg, exc_info=error, extra=kw)
        else:
            self._logger.error(msg, extra=kw)

    def log_debug(self, message: str, **kwargs: Any) -> None:
        msg, kw = self._prepare(message, kwargs)
        self._logger.debug(msg, extra=kw)

    def set_log_level(self, level: str) -> None:
        self._logger.setLevel(level)
        self._level = level

    def get_log_level(self) -> str:
        return logging.getLevelName(self._logger.level)


def configure_logging(level: str = "INFO") -> LoggingService:
    """Return a configured :class:`LoggingService` instance."""

    return LoggingService(level=level)


__all__ = ["LoggingService", "configure_logging"]

