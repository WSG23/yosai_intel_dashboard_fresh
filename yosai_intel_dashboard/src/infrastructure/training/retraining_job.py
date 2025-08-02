"""Scheduled retraining job using APScheduler."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Tuple

import pandas as pd

try:  # pragma: no cover - optional dependency
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:  # pragma: no cover
    BackgroundScheduler = None  # type: ignore

from yosai_intel_dashboard.src.models.ml.training.pipeline import TrainingPipeline
from yosai_intel_dashboard.models.ml.feature_store import FeastFeatureStore

logger = logging.getLogger(__name__)


class RetrainingJob:
    """Periodically trigger model retraining based on time or data volume."""

    def __init__(
        self,
        pipeline: TrainingPipeline,
        entity_df_supplier: Callable[[], pd.DataFrame],
        feature_service: Any,
        models: Dict[str, Tuple[Any, Dict[str, Any]]],
        target_column: str,
        *,
        feature_store: FeastFeatureStore | None = None,
        schedule_interval_minutes: int = 60,
        row_threshold: int = 1000,
    ) -> None:
        self.pipeline = pipeline
        self.entity_df_supplier = entity_df_supplier
        self.feature_service = feature_service
        self.models = models
        self.target_column = target_column
        self.feature_store = feature_store
        self.schedule_interval_minutes = schedule_interval_minutes
        self.row_threshold = row_threshold
        self.scheduler = BackgroundScheduler() if BackgroundScheduler else None

    # ------------------------------------------------------------------
    def _should_retrain(self, entity_df: pd.DataFrame) -> bool:
        if not self.feature_store:
            return True
        df = self.feature_store.get_training_dataframe(self.feature_service, entity_df)
        return len(df) >= self.row_threshold

    def _run(self) -> None:
        entity_df = self.entity_df_supplier()
        if not self._should_retrain(entity_df):
            logger.info("Retraining skipped: insufficient new data")
            return
        self.pipeline.run(
            entity_df,
            target_column=self.target_column,
            models=self.models,
            feature_store=self.feature_store,
            feature_service=self.feature_service,
        )

    # ------------------------------------------------------------------
    def start(self) -> None:
        if not self.scheduler:
            raise RuntimeError("APScheduler is required for RetrainingJob")
        self.scheduler.add_job(self._run, "interval", minutes=self.schedule_interval_minutes)
        self.scheduler.start()

    def stop(self) -> None:
        if self.scheduler:
            self.scheduler.shutdown()


__all__ = ["RetrainingJob"]
