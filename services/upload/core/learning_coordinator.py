import logging
from typing import Dict

import pandas as pd

from services.upload.protocols import DeviceLearningServiceProtocol

logger = logging.getLogger(__name__)


class LearningCoordinator:
    """Coordinate device learning operations."""

    def __init__(self, service: DeviceLearningServiceProtocol) -> None:
        self.service = service

    def user_mappings(self, filename: str) -> Dict[str, any]:
        try:
            return self.service.get_user_device_mappings(filename) or {}
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Failed to load user mappings for %s: %s", filename, exc)
            return {}

    def auto_apply(self, df: pd.DataFrame, filename: str) -> bool:
        try:
            learned = self.service.get_learned_mappings(df, filename)
            if learned:
                self.service.apply_learned_mappings_to_global_store(df, filename)
                logger.info("🤖 Auto-applied %s learned device mappings", len(learned))
                return True
            return False
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Failed to auto-apply learned mappings: %s", exc)
            return False
