from __future__ import annotations

import logging
from logging.config import dictConfig

LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


def configure_logging(level: int | str = "INFO") -> None:
    """Apply default logging configuration.

    Parameters
    ----------
    level:
        Logging level for the root logger.
    """
    config = dict(LOGGING_CONFIG)
    config["root"] = dict(config["root"], level=level)
    dictConfig(config)
