from __future__ import annotations
import json, logging, os, sys, time
from typing import Any, Dict

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "lvl": record.levelname,
            "ts": int(time.time()*1000),
            "msg": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)

def configure(level: str | int = None) -> None:
    lvl = level or os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    if root.handlers:  # idempotent
        for h in root.handlers: h.setFormatter(JsonFormatter())
        root.setLevel(lvl)
        return
    h = logging.StreamHandler(stream=sys.stdout)
    h.setFormatter(JsonFormatter())
    root.addHandler(h)
    root.setLevel(lvl)

def get_logger(name: str) -> logging.Logger:
    configure()  # safe to call many times
    return logging.getLogger(name)
