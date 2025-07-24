import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Lightweight client for querying the active AI model version."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (
            base_url or os.getenv("MODEL_REGISTRY_URL", "http://localhost:8080")
        ).rstrip("/")
        self.session = requests.Session()

    def get_active_version(
        self, model_name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Return the active version for *model_name* or *default* if lookup fails."""
        try:
            resp = self.session.get(
                f"{self.base_url}/models/{model_name}/active", timeout=2
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("version", default)
        except Exception as exc:  # pragma: no cover - network failures
            logger.warning("model registry lookup failed for %s: %s", model_name, exc)
            return default


__all__ = ["ModelRegistry"]
