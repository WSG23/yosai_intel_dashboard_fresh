"""Re-export logging utilities."""

from ..infrastructure.logging.setup import LoggingService

__all__ = ["LoggingService"]


# --- injected dev helper: safe get_logger to avoid circular import issues ---
import logging as _py_logging

def get_logger(name: str | None = None):
    logger = _py_logging.getLogger(name or "yosai")
    if not logger.handlers:
        _py_logging.basicConfig(
            level=_py_logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    return logger
