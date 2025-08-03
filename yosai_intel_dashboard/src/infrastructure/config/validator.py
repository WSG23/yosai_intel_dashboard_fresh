from dataclasses import dataclass
from typing import List


@dataclass
class YosaiConfig:
    """Simplified configuration proto used across services."""

    service_name: str
    log_level: str = "INFO"
    metrics_addr: str = ""
    tracing_endpoint: str = ""
    tracing_exporter: str = "jaeger"


class ConfigValidator:
    """Validate :class:`YosaiConfig` instances."""

    _LEVELS = {"DEBUG", "INFO", "WARN", "ERROR"}

    def validate(self, cfg: YosaiConfig) -> List[str]:
        errors: List[str] = []
        if not cfg.service_name:
            errors.append("service_name is required")

        if cfg.log_level.upper() not in self._LEVELS:
            errors.append("log_level must be one of " + ", ".join(sorted(self._LEVELS)))

        if cfg.metrics_addr:
            host_port = cfg.metrics_addr.rsplit(":", 1)
            if len(host_port) != 2:
                errors.append("metrics_addr must be in host:port format")
            else:
                port = host_port[1]
                if not port.isdigit() or not (1 <= int(port) <= 65535):
                    errors.append("metrics_addr port must be 1-65535")
        elif cfg.log_level.upper() == "DEBUG":
            errors.append("metrics_addr required when log_level is DEBUG")

        if cfg.tracing_endpoint and not cfg.tracing_endpoint.startswith(
            ("http://", "https://")
        ):
            errors.append("tracing_endpoint must start with http:// or https://")

        if cfg.tracing_exporter.lower() not in {"jaeger", "zipkin"}:
            errors.append("tracing_exporter must be 'jaeger' or 'zipkin'")

        if cfg.metrics_addr and cfg.metrics_addr == cfg.tracing_endpoint:
            errors.append("metrics_addr and tracing_endpoint must differ")

        return errors


def validate_config(cfg: YosaiConfig) -> List[str]:
    """Return validation errors for ``cfg``."""
    return ConfigValidator().validate(cfg)
