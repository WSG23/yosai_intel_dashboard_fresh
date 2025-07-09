import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .environment import select_config_file

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load configuration data from YAML files."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path

    def load(self) -> Dict[str, Any]:
        """Return configuration dictionary from YAML or empty dict."""
        config_file = select_config_file(self.config_path)
        if not config_file or not Path(config_file).exists():
            logger.info("No YAML config file found, using defaults")
            return {}
        try:
            with open(config_file, "r", encoding="utf-8") as fh:
                content = fh.read()
                # simple env substitution
                import re

                def replacer(match: re.Match[str]) -> str:
                    var = match.group(1)
                    return os.getenv(var, match.group(0))

                content = re.sub(r"\$\{([^}]+)\}", replacer, content)

                class IncludeLoader(yaml.SafeLoader):
                    pass

                base_dir = Path(config_file).parent

                def _include(loader: IncludeLoader, node: yaml.Node) -> Any:
                    filename = loader.construct_scalar(node)
                    inc_path = base_dir / filename
                    with open(inc_path, "r", encoding="utf-8") as inc:
                        return yaml.load(inc, Loader=IncludeLoader)

                IncludeLoader.add_constructor("!include", _include)

                data = yaml.load(content, Loader=IncludeLoader)
                return data or {}
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Error loading config file %s: %s", config_file, exc)
            return {}
