from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class DeviceLearningServiceProtocol(Protocol):
    """Interface for persistent device learning services."""

    def get_learned_mappings(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict]:
        """Retrieve learned device mappings for ``filename``."""
        ...

    def apply_learned_mappings_to_global_store(
        self, df: pd.DataFrame, filename: str
    ) -> bool:
        """Apply learned device mappings to the global AI mapping store."""
        ...

    def get_user_device_mappings(self, filename: str) -> Dict[str, Any]:
        """Return user confirmed mappings for ``filename`` if available."""
        ...

    def save_user_device_mappings(
        self, df: pd.DataFrame, filename: str, user_mappings: Dict[str, Any]
    ) -> bool:
        """Persist user confirmed mappings for future use."""
        ...


__all__ = ["DeviceLearningServiceProtocol"]
