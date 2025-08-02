from __future__ import annotations

"""Utilities for comparing model versions and triggering rollbacks."""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

from packaging.version import Version
from sqlalchemy import select
from sqlalchemy.orm import Session

from yosai_intel_dashboard.src.services.timescale.models import ModelVersionMetric


@dataclass
class ModelPerformanceTracker:
    """Persist and compare model metrics across versions."""

    session: Session
    rollback_hook: Optional[Callable[[str, str], None]] = None
    canary_hook: Optional[Callable[[str, str], None]] = None

    # ------------------------------------------------------------------
    def record_metrics(self, model_name: str, version: str, metrics: Dict[str, float]) -> None:
        """Store ``metrics`` for ``model_name`` and ``version``."""
        now = datetime.utcnow()
        for metric, value in metrics.items():
            self.session.add(
                ModelVersionMetric(
                    time=now,
                    model_name=model_name,
                    version=version,
                    metric=metric,
                    value=value,
                )
            )
        self.session.commit()

    # ------------------------------------------------------------------
    def _available_versions(self, model_name: str) -> List[str]:
        stmt = select(ModelVersionMetric.version).where(
            ModelVersionMetric.model_name == model_name
        ).distinct()
        return [row[0] for row in self.session.execute(stmt)]

    def _metrics_for(self, model_name: str, version: str) -> Dict[str, float]:
        stmt = select(ModelVersionMetric.metric, ModelVersionMetric.value).where(
            ModelVersionMetric.model_name == model_name,
            ModelVersionMetric.version == version,
        )
        return {metric: value for metric, value in self.session.execute(stmt)}

    def compare(
        self, model_name: str, current_version: str
    ) -> Optional[Tuple[Dict[str, float], Dict[str, float], str]]:
        """Return metrics for ``current_version`` and its previous version."""
        versions = [Version(v) for v in self._available_versions(model_name)]
        prev_versions = [v for v in versions if v < Version(current_version)]
        if not prev_versions:
            return None
        prev_version = max(prev_versions).public
        current_metrics = self._metrics_for(model_name, current_version)
        previous_metrics = self._metrics_for(model_name, prev_version)
        return current_metrics, previous_metrics, prev_version

    # ------------------------------------------------------------------
    def evaluate(
        self, model_name: str, current_version: str, *, threshold: float = 0.0
    ) -> bool:
        """Compare metrics and trigger hooks.

        Returns ``True`` if a rollback was triggered, ``False`` otherwise."""
        comparison = self.compare(model_name, current_version)
        if comparison is None:
            if self.canary_hook:
                self.canary_hook(model_name, current_version)
            return False
        current, previous, prev_version = comparison
        for metric, cur_value in current.items():
            prev_value = previous.get(metric)
            if prev_value is not None and cur_value + threshold < prev_value:
                if self.rollback_hook:
                    self.rollback_hook(model_name, prev_version)
                return True
        if self.canary_hook:
            self.canary_hook(model_name, current_version)
        return False


__all__ = ["ModelPerformanceTracker"]

