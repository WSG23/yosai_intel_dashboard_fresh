"""Feast feature store integration for ML pipelines."""

from __future__ import annotations

import logging
from typing import Dict, List

import pandas as pd
from feast import FeatureService, FeatureStore

logger = logging.getLogger(__name__)


class FeastFeatureStore:
    """Wrapper around :class:`feast.FeatureStore` with drift monitoring."""

    def __init__(self, repo_path: str = "feature_store") -> None:
        self.store = FeatureStore(repo_path=repo_path)

    # ------------------------------------------------------------------
    def get_training_dataframe(
        self, feature_service: FeatureService, entity_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Retrieve historical features for model training."""
        return (
            self.store.get_historical_features(
                entity_df=entity_df, features=feature_service
            )
            .to_df()
            .sort_values("event_timestamp")
            .reset_index(drop=True)
        )

    def get_online_features(
        self, feature_service: FeatureService, entity_rows: List[Dict]
    ) -> Dict[str, List]:
        """Retrieve online features for realtime inference."""
        return self.store.get_online_features(
            features=feature_service, entity_rows=entity_rows
        ).to_dict()

    # ------------------------------------------------------------------
    def monitor_feature_drift(
        self, current: pd.DataFrame, baseline: pd.DataFrame, threshold: float = 0.1
    ) -> Dict[str, float]:
        """Simple mean drift monitoring for each column."""
        drifts: Dict[str, float] = {}
        for col in current.columns:
            if col not in baseline.columns:
                continue
            diff = abs(current[col].mean() - baseline[col].mean())
            drifts[col] = diff
            if diff > threshold:
                logger.warning("Feature drift detected for %s: %.4f", col, diff)
        return drifts


__all__ = ["FeastFeatureStore"]
