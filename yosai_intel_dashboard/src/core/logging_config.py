"""Enhanced logging configuration"""

import json
import logging
import logging.config
from datetime import datetime
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
            ]:
                log_entry[key] = value

        return json.dumps(log_entry)


def setup_logging(config: Dict[str, Any]) -> None:
    """Setup application logging"""

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
            "json": {"()": JsonFormatter},
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/app.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "json",
                "encoding": "utf-8",
                "errors": "backslashreplace",
            },
        },
        "loggers": {
            "": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
            "yosai": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }

    if config.get("debug", False):
        logging_config["handlers"]["console"]["level"] = "DEBUG"

    logging.config.dictConfig(logging_config)
