from __future__ import annotations

from typing import Any, Dict

import pandas as pd


class AIColumnMapperAdapter:
    """Thin wrapper around the :class:`ComponentPluginAdapter` plugin system."""

    def __init__(self, adapter: Any | None = None) -> None:
        if adapter is None:
            from components.plugin_adapter import ComponentPluginAdapter

            adapter = ComponentPluginAdapter()
        self._adapter = adapter

    def suggest(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict[str, Any]]:
        """Return AI suggestions for *df* columns."""
        return self._adapter.get_ai_column_suggestions(df, filename)

    def confirm(
        self, filename: str, mapping: Dict[str, str], metadata: Dict[str, Any]
    ) -> bool:
        """Store confirmed column mapping for *filename*."""
        return self._adapter.save_verified_mappings(filename, mapping, metadata)
