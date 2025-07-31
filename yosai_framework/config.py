import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import jsonschema
import yaml

from yosai_intel_dashboard.src.infrastructure.config.validator import YosaiConfig, validate_config

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "config" / "service.schema.yaml"


@dataclass
class ServiceConfig:
    service_name: str
    log_level: str = "INFO"
    metrics_addr: str = ""
    tracing_endpoint: str = ""
    enable_profiling: bool = False


def load_config(path: str) -> ServiceConfig:
    data: Dict[str, Any] = {}
    if path:
        data = yaml.safe_load(Path(path).read_text())
    with open(SCHEMA_PATH) as f:
        schema = yaml.safe_load(f)
    jsonschema.validate(data, schema)
    for key, value in os.environ.items():
        if key.startswith("YOSAI_"):
            data[key[6:].lower()] = value

    cfg = ServiceConfig(**data)
    if isinstance(cfg.enable_profiling, str):
        cfg.enable_profiling = cfg.enable_profiling.lower() in {"1", "true", "yes"}
    errors = validate_config(
        YosaiConfig(
            service_name=cfg.service_name,
            log_level=cfg.log_level,
            metrics_addr=cfg.metrics_addr,
            tracing_endpoint=cfg.tracing_endpoint,
        )
    )
    if errors:
        raise ValueError("; ".join(errors))
    return cfg
