from __future__ import annotations

from typing import Callable

from .service import BaseService


class ServiceBuilder:
    """Build ``BaseService`` instances with optional features."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.config_path = ""
        self._logging = False
        self._log_level = "INFO"
        self._metrics = False
        self._metrics_addr = ""
        self._health = False

    def with_config(self, path: str) -> "ServiceBuilder":
        self.config_path = path
        return self

    def with_logging(self, level: str = "INFO") -> "ServiceBuilder":
        self._logging = True
        self._log_level = level
        return self

    def with_metrics(self, addr: str = "") -> "ServiceBuilder":
        self._metrics = True
        self._metrics_addr = addr
        return self

    def with_health(self) -> "ServiceBuilder":
        self._health = True
        return self

    def build(self) -> BaseService:
        service = BaseService(self.name, self.config_path)

        if self._logging:
            service.config.log_level = self._log_level
        else:
            service._setup_logging = lambda: None  # type: ignore[assignment]

        if self._metrics:
            service.config.metrics_addr = self._metrics_addr
        else:
            service._setup_metrics = lambda: None  # type: ignore[assignment]

        if not self._health:
            service.app.router.routes = [
                r
                for r in service.app.router.routes
                if not getattr(r, "path", "").startswith("/health")
            ]

        return service
