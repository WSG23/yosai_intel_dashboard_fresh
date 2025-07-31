"""Load YAML or JSON configuration into protobuf structures."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from google.protobuf import json_format

from .base_loader import BaseConfigLoader
from .environment_processor import EnvironmentProcessor
from .generated.protobuf.config.schema import config_pb2


class UnifiedLoader(BaseConfigLoader):
    """Load configuration and return :class:`YosaiConfig` message."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path

    def _read_source(self, path: Path) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if path.exists():
            data = self.load_file(path)
        elif env_json := os.getenv("YOSAI_CONFIG_JSON"):
            try:
                data = json.loads(env_json)
            except Exception:  # pragma: no cover - defensive
                pass
        return data

    def load(self, config_path: Optional[str] = None) -> config_pb2.YosaiConfig:
        path = Path(config_path or self.config_path or "config/config.yaml")
        cfg_dict = self._read_source(path)
        message = config_pb2.YosaiConfig()
        json_format.ParseDict(cfg_dict, message, ignore_unknown_fields=True)
        processor = EnvironmentProcessor()
        processor.apply(message)
        return message


__all__ = ["UnifiedLoader"]
