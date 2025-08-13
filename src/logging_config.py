"""Application logging configuration with JSON structured logs."""

from __future__ import annotations

import json
import logging
import logging.config
from datetime import datetime
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """Format logs as JSON without PII."""

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - trivial
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in {
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
            }:
                log_entry[key] = value
        return json.dumps(log_entry)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger for structured logging."""

    config: Dict[str, Any] = {
        "version": 1,
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": level,
            }
        },
        "root": {"handlers": ["console"], "level": level},
    }
    logging.config.dictConfig(config)
