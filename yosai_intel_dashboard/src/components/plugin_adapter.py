"""Adapter for optional AI plugins.

This adapter communicates with a plugin service if available. Network
failures are swallowed and logged via :class:`ErrorHandler` so callers receive
empty results instead of exceptions. This allows UI components to display
placeholder states when the plugin backend is unavailable.
"""

from __future__ import annotations

import os
from typing import Any, Dict

import pandas as pd
import requests

from yosai_intel_dashboard.src.error_handling import ErrorHandler


class ComponentPluginAdapter:
    """Thin HTTP client for plugin-provided AI helpers."""

    def __init__(
        self,
        base_url: str | None = None,
        handler: ErrorHandler | None = None,
    ) -> None:
        self.base_url = base_url or os.getenv(
            "PLUGIN_SERVICE_URL", "http://localhost:8003"
        )
        self.error_handler = handler or ErrorHandler()

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _post(self, path: str, payload: Dict[str, Any]) -> Any:
        try:
            resp = requests.post(
                f"{self.base_url}{path}", json=payload, timeout=2
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # pragma: no cover - network failures
            self.error_handler.handle(exc)
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def suggest_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Return simple column rename suggestions.

        The plugin service is asked for suggestions based on the provided
        DataFrame. If the request fails an empty mapping is returned.
        """

        result = self._post(
            "/v1/ai/suggest-columns", {"columns": list(df.columns)}
        )
        if isinstance(result, dict):
            return {k: str(v) for k, v in result.items()}
        return {}

    def get_ai_column_suggestions(
        self, df: pd.DataFrame, filename: str
    ) -> Dict[str, Dict[str, Any]]:
        """Return detailed AI suggestions for column mappings."""

        result = self._post(
            "/v1/ai/column-suggestions",
            {"columns": list(df.columns), "filename": filename},
        )
        if isinstance(result, dict):
            return result
        return {}

    def save_verified_mappings(
        self, filename: str, mappings: Dict[str, str], metadata: Dict[str, Any]
    ) -> bool:
        """Persist user-confirmed column mappings."""

        result = self._post(
            "/v1/ai/save-mappings",
            {"filename": filename, "mappings": mappings, "metadata": metadata},
        )
        return bool(result)

    def get_ai_plugin(self):
        """Return an instance of the AI plugin if it can be imported."""

        try:
            from yosai_intel_dashboard.src.adapters.api.plugins.ai_classification.plugin import (
                AIClassificationPlugin,
            )

            plugin = AIClassificationPlugin()
            plugin.start()
            return plugin
        except Exception as exc:  # pragma: no cover - optional dependency
            self.error_handler.handle(exc)
            return None


__all__ = ["ComponentPluginAdapter"]

