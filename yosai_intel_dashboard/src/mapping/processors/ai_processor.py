from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from core.container import container as default_container
from core.service_container import ServiceContainer
from mapping.models import HeuristicMappingModel, MappingModel


class AIColumnMapperAdapter:
    """Wrapper using a mapping model resolved from the service container."""

    def __init__(
        self,
        adapter: Any | None = None,
        *,
        container: Any | None = None,
        default_model: str = "default",
    ) -> None:

        if adapter is None:
            from yosai_intel_dashboard.src.components.plugin_adapter import (
                ComponentPluginAdapter,
            )

            adapter = ComponentPluginAdapter()
        if container is None:
            container = ServiceContainer()
        self._adapter = adapter
        self._container = container or default_container
        self._default_model = default_model

    def _get_model(self, key: str) -> MappingModel:
        svc_key = f"mapping_model:{key}"
        if self._container and self._container.has(svc_key):
            return self._container.get(svc_key)
        return HeuristicMappingModel()

    def suggest(
        self, df: pd.DataFrame, filename: str, model_key: str | None = None
    ) -> Dict[str, Dict[str, Any]]:
        """Return AI suggestions for *df* columns."""
        model = self._get_model(model_key or self._default_model)
        try:
            return model.suggest(df, filename)
        except Exception:  # pragma: no cover - fall back
            return self._adapter.get_ai_column_suggestions(df, filename)

    def confirm(
        self, filename: str, mapping: Dict[str, str], metadata: Dict[str, Any]
    ) -> bool:
        """Store confirmed column mapping for *filename*."""
        return self._adapter.save_verified_mappings(filename, mapping, metadata)
