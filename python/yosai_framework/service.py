import logging
import signal
from typing import Any

from .config import ServiceConfig, load_config


class BaseService:
    """Basic service with logging, metrics, tracing and signal handling."""

    def __init__(self, name: str, config_path: str):
        self.name = name
        self.config: ServiceConfig = load_config(config_path)
        self.log = logging.getLogger(name)
        self.running = False

    def start(self) -> None:
        self._setup_logging()
        self._setup_metrics()
        self._setup_tracing()
        self._setup_signals()
        self.running = True
        self.log.info("service %s started", self.name)

    # ------------------------------------------------------------------
    def stop(self, *_: Any) -> None:
        if self.running:
            self.running = False
            self.log.info("service %s stopping", self.name)

    # ------------------------------------------------------------------
    def _setup_logging(self) -> None:
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(level=level)

    def _setup_metrics(self) -> None:  # pragma: no cover - placeholder
        # Metrics initialization would go here
        pass

    def _setup_tracing(self) -> None:  # pragma: no cover - placeholder
        # Tracing initialization would go here
        pass

    def _setup_signals(self) -> None:
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)
