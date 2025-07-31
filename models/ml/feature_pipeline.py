from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd
import yaml
from joblib import Parallel, delayed
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.inspection import permutation_importance

from analytics.feature_extraction import extract_event_features
from yosai_intel_dashboard.models.ml.feature_store import FeastFeatureStore
from yosai_intel_dashboard.models.ml.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


@dataclass
class TransformerEntry:
    transformer: TransformerMixin
    columns: List[str]


class FeaturePipeline(BaseEstimator, TransformerMixin):
    """Feature engineering pipeline with Feast integration and versioning."""

    def __init__(
        self,
        defs_path: str | Path,
        *,
        feature_store: FeastFeatureStore | None = None,
        registry: ModelRegistry | None = None,
        n_jobs: int = 1,
    ) -> None:
        self.defs_path = Path(defs_path)
        self.feature_store = feature_store
        self.registry = registry
        self.n_jobs = n_jobs
        self.transformers: Dict[str, TransformerEntry] = {}
        self.feature_list: List[str] = []
        self.version: str | None = None

    # ------------------------------------------------------------------
    def load_definitions(self) -> None:
        """Load feature definitions from JSON or YAML."""
        if not self.defs_path.exists():
            raise FileNotFoundError(str(self.defs_path))
        if self.defs_path.suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(self.defs_path.read_text())
        else:
            data = json.loads(self.defs_path.read_text())
        self.feature_list = list(data.get("features", []))
        logger.info("Loaded %d feature definitions", len(self.feature_list))

    # ------------------------------------------------------------------
    def register_transformer(
        self, name: str, transformer: TransformerMixin, columns: Iterable[str]
    ) -> None:
        """Register a transformer for later execution."""
        self.transformers[name] = TransformerEntry(transformer, list(columns))

    # ------------------------------------------------------------------
    def fit(self, X: pd.DataFrame, y: Any | None = None) -> "FeaturePipeline":
        df = extract_event_features(X)
        if not self.feature_list:
            self.feature_list = df.columns.tolist()
        Parallel(n_jobs=self.n_jobs)(
            delayed(entry.transformer.fit)(df[entry.columns], y)
            for entry in self.transformers.values()
        )
        return self

    # ------------------------------------------------------------------
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = extract_event_features(X)
        for entry in self.transformers.values():
            transformed = entry.transformer.transform(df[entry.columns])
            if isinstance(transformed, pd.DataFrame):
                df[entry.columns] = transformed
            else:
                df[entry.columns] = pd.DataFrame(transformed, index=df.index)
        return df[self.feature_list]

    # ------------------------------------------------------------------
    def fit_transform(self, X: pd.DataFrame, y: Any | None = None) -> pd.DataFrame:
        self.fit(X, y)
        return self.transform(X)

    # ------------------------------------------------------------------
    def compute_batch_features(
        self, service: Any, entity_df: pd.DataFrame
    ) -> pd.DataFrame:
        if not self.feature_store:
            raise ValueError("feature_store not configured")
        return self.feature_store.get_training_dataframe(service, entity_df)

    def compute_online_features(
        self, service: Any, entity_rows: List[Dict[str, Any]]
    ) -> Dict[str, List]:
        if not self.feature_store:
            raise ValueError("feature_store not configured")
        return self.feature_store.get_online_features(service, entity_rows)

    # ------------------------------------------------------------------
    def feature_importance(
        self, model: Any, X: pd.DataFrame, y: pd.Series
    ) -> pd.DataFrame:
        result = permutation_importance(model, X, y, n_jobs=self.n_jobs)
        return pd.DataFrame(
            {
                "feature": X.columns,
                "importance": result.importances_mean,
            }
        ).sort_values("importance", ascending=False)

    # ------------------------------------------------------------------
    def detect_drift(
        self, current: pd.DataFrame, baseline: pd.DataFrame, threshold: float = 0.1
    ) -> Dict[str, float]:
        drifts: Dict[str, float] = {}
        for col in current.columns:
            if col not in baseline.columns:
                continue
            diff = abs(current[col].mean() - baseline[col].mean())
            if diff > threshold:
                drifts[col] = diff
        return drifts

    # ------------------------------------------------------------------
    def register_version(
        self,
        name: str,
        model_path: str,
        metrics: Dict[str, float],
        dataset_hash: str,
    ) -> str:
        if not self.registry:
            raise ValueError("registry not configured")
        record = self.registry.register_model(
            name,
            model_path,
            metrics,
            dataset_hash,
        )
        self.registry.set_active_version(name, record.version)
        self.version = record.version
        return record.version

    def rollback(self, name: str, version: str) -> None:
        if not self.registry:
            raise ValueError("registry not configured")
        self.registry.set_active_version(name, version)
        self.version = version


__all__ = ["FeaturePipeline"]
