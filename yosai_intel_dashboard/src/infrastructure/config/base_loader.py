import io
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml


class BaseConfigLoader:
    """Generic loader for YAML or JSON configuration files."""

    log = logging.getLogger(__name__)

    def load_file(self, path: Path) -> Dict[str, Any]:
        """Load and sanitize configuration from ``path``."""
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = self._load_yaml(path)
        elif path.suffix.lower() == ".json":
            data = self._load_json(path)
        else:
            data = {}
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
        text = self._substitute_env_vars(path.read_text(encoding="utf-8"))
        return json.loads(text)

    def _substitute_env_vars(self, text: str) -> str:
        import re

        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            return os.getenv(key, match.group(0))

        return re.sub(r"\$\{([^}]+)\}", repl, text)

    def _sanitize(self, obj: Any) -> Any:
        if isinstance(obj, str):
            try:
                from core.unicode import UnicodeSQLProcessor

                return UnicodeSQLProcessor.encode_query(obj)
            except Exception:
                return obj
        if isinstance(obj, dict):
            return {k: self._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._sanitize(v) for v in obj]
        return obj


__all__ = ["BaseConfigLoader"]
