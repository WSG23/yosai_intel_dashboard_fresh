import logging
import signal
from typing import Any

from fastapi import FastAPI, HTTPException

from .config import ServiceConfig, load_config


class BaseService:
    """Basic service with logging, metrics, tracing and signal handling."""

    def __init__(self, name: str, config_path: str):
        self.name = name
        self.config: ServiceConfig = load_config(config_path)
        self.log = logging.getLogger(name)
        self.running = False
        self.app = FastAPI(title=name)
        self.app.state.ready = False
        self.app.state.live = True
        self.app.state.startup_complete = False
        self._add_health_routes()

    def start(self) -> None:
        self._setup_logging()
        self._setup_metrics()
        self._setup_tracing()
        self._setup_signals()
        self.running = True
        self.app.state.startup_complete = True
        self.app.state.ready = True
        self.log.info("service %s started", self.name)

    # ------------------------------------------------------------------
    def stop(self, *_: Any) -> None:
        if self.running:
            self.running = False
            self.app.state.ready = False
            self.app.state.live = False
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

    # ------------------------------------------------------------------
    def _add_health_routes(self) -> None:
        @self.app.get("/health")
        async def _health() -> dict[str, str]:
            return {"status": "ok"}

        @self.app.get("/health/live")
        async def _health_live() -> dict[str, str]:
            return {"status": "ok" if self.app.state.live else "shutdown"}

        @self.app.get("/health/ready")
        async def _health_ready() -> dict[str, str]:
            if self.app.state.ready:
                return {"status": "ready"}
            raise HTTPException(status_code=503, detail="not ready")

        @self.app.get("/health/startup")
        async def _health_startup() -> dict[str, str]:
            if self.app.state.startup_complete:
                return {"status": "complete"}
            raise HTTPException(status_code=503, detail="starting")
