from __future__ import annotations

from typing import Any, Dict

import pandas as pd


from core.service_container import ServiceContainer
from mapping.models import MappingModel


class AIColumnMapperAdapter:
    """Resolve the active :class:`MappingModel` via the DI container."""

    def __init__(
        self,
        adapter: Any | None = None,
        container: ServiceContainer | None = None,
    ) -> None:
        if adapter is None:
            from components.plugin_adapter import ComponentPluginAdapter

            adapter = ComponentPluginAdapter()
        if container is None:
            container = ServiceContainer()
        self._adapter = adapter
        self._container = container

    # ------------------------------------------------------------------
    def _get_model(self) -> MappingModel | None:
        try:
            return self._container.get("mapping_model", MappingModel)
        except Exception:
            return None

    def suggest(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict[str, Any]]:
        """Return suggestions using the active mapping model if available."""
        model = self._get_model()
        if model is not None:
            result = model.cached_suggest(df, filename)
            if any(v.get("field") for v in result.values()):
                return result
        # Fallback to simple heuristics if no model or empty result
        return self._adapter.get_ai_column_suggestions(df, filename)

    def confirm(
        self, filename: str, mapping: Dict[str, str], metadata: Dict[str, Any]
    ) -> bool:
        """Store confirmed column mapping for *filename*."""
        return self._adapter.save_verified_mappings(filename, mapping, metadata)
