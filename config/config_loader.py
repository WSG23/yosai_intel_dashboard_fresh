"""Load configuration files with YAML ``!include`` support."""

from __future__ import annotations

import io
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .environment import select_config_file
from .protocols import ConfigLoaderProtocol
from .unicode_sql_processor import UnicodeSQLProcessor


class ConfigLoader(ConfigLoaderProtocol):
    """Load configuration from YAML/JSON files or environment.

    The loader understands a custom ``!include`` YAML tag which allows other
    YAML files to be recursively included relative to the current file.
    """

    log = logging.getLogger(__name__)

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path

    def load(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        path = select_config_file(config_path or self.config_path)
        data: Dict[str, Any] = {}
        if path and path.exists():
            try:
                if path.suffix.lower() in {".yaml", ".yml"}:
                    data = self._load_yaml(path)
                elif path.suffix.lower() == ".json":
                    data = self._load_json(path)
            except Exception as exc:  # pragma: no cover - defensive
                self.log.warning("Failed to load %s: %s", path, exc)

        env_json = os.getenv("YOSAI_CONFIG_JSON")
        if not data and env_json:
            try:
                data = json.loads(env_json)
            except Exception as exc:  # pragma: no cover - defensive
                self.log.warning("Failed to parse YOSAI_CONFIG_JSON: %s", exc)
        return self._sanitize(data)

    # ------------------------------------------------------------------
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        def _recursive_load(file_path: Path) -> Any:
            class Loader(yaml.SafeLoader):
                pass

            def _include(loader: Loader, node: yaml.Node) -> Any:
                filename = loader.construct_scalar(node)
                inc_path = (loader._root / filename).resolve()
                return _recursive_load(inc_path)

            Loader.add_constructor("!include", _include)

            text = self._substitute_env_vars(file_path.read_text(encoding="utf-8"))
            loader = Loader(io.StringIO(text))
            loader._root = file_path.parent
            try:
                return loader.get_single_data() or {}
            finally:
                loader.dispose()

        return _recursive_load(path)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _substitute_env_vars(self, text: str) -> str:
        import re

        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            return os.getenv(key, match.group(0))

        return re.sub(r"\$\{([^}]+)\}", repl, text)

    def _sanitize(self, obj: Any) -> Any:
        if isinstance(obj, str):
            try:
                return UnicodeSQLProcessor.encode_query(obj)
            except Exception:
                return obj
        if isinstance(obj, dict):
            return {k: self._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._sanitize(v) for v in obj]
        return obj


__all__ = ["ConfigLoader", "ConfigLoaderProtocol"]
