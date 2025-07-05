"""Helper adapter exposing plugin services to UI components."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from core.plugins.service_locator import PluginServiceLocator
from services.data_enhancer import get_ai_column_suggestions


logger = logging.getLogger(__name__)


class ComponentPluginAdapter:
    """Adapter providing safe access to optional plugin services."""

    def get_ai_plugin(self):
        return PluginServiceLocator.get_ai_classification_service()

    # ------------------------------------------------------------------
    # AI column mapping helpers
    # ------------------------------------------------------------------
    def get_ai_column_suggestions(
        self, df: pd.DataFrame, filename: str
    ) -> Dict[str, Dict[str, Any]]:
        plugin = self.get_ai_plugin()
        headers = df.columns.tolist()
        if plugin and hasattr(plugin, "map_columns"):
            try:
                session_id = f"file_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                result = plugin.map_columns(headers, session_id)
                if result.get("success"):
                    mapping = result.get("suggested_mapping", {})
                    scores = result.get("confidence_scores", {})
                    return {
                        h: {"field": mapping.get(h, ""), "confidence": scores.get(h, 0.0)}
                        for h in headers
                    }
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("AI suggestion failed: %s", exc)
        # Fallback to simple heuristics
        return get_ai_column_suggestions(headers)

    def save_verified_mappings(
        self, filename: str, mappings: Dict[str, str], metadata: Dict[str, Any]
    ) -> bool:
        plugin = self.get_ai_plugin()
        if plugin and hasattr(plugin, "confirm_column_mapping"):
            try:
                session_id = f"verified_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                plugin.confirm_column_mapping(mappings, session_id)
                if getattr(plugin, "csv_repository", None):
                    plugin.csv_repository.store_column_mapping(session_id, {
                        "filename": filename,
                        "mappings": mappings,
                        "metadata": metadata,
                        "timestamp": datetime.now().isoformat(),
                    })
                return True
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("Saving verified mappings failed: %s", exc)
        return False



__all__ = ["ComponentPluginAdapter"]
