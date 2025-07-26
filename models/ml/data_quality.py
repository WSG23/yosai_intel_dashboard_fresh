"""Comprehensive data quality utilities for ML pipelines."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, Iterable, Iterator, List, Optional, Type

import numpy as np
import pandas as pd
from pydantic import BaseModel, ValidationError

from core.unicode import UnicodeProcessor
from monitoring.data_quality_monitor import DataQualityMetrics, get_data_quality_monitor

try:  # Optional dependency
    from sklearn.ensemble import IsolationForest
except Exception:  # pragma: no cover - optional
    IsolationForest = None

try:  # Optional dependency
    from scipy import stats as scipy_stats
except Exception:  # pragma: no cover - optional
    scipy_stats = None

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------
class AccessEventModel(BaseModel):
    """Example schema for access events."""

    timestamp: Any
    person_id: str
    door_id: str
    access_result: Any


@dataclass
class DriftResult:
    """Result of a data drift comparison."""

    column: str
    statistic: float
    p_value: float


# ---------------------------------------------------------------------------
class DataQualityFramework:
    """Unified framework for validating and monitoring data quality."""

    def __init__(self, model: Type[BaseModel] = AccessEventModel) -> None:
        self.model = model
        self.monitor = get_data_quality_monitor()
        self.history: List[DataQualityMetrics] = []

    # ------------------------------------------------------------------
    def _validate_row(self, record: Dict[str, Any]) -> Dict[str, Any]:
        try:
            obj = self.model.model_validate(record)
            return obj.model_dump()
        except ValidationError as exc:  # pragma: no cover - runtime logging
            logger.debug("Schema validation failed: %s", exc)
            return {}

    def validate_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return ``df`` rows that conform to the Pydantic schema."""
        cleaned: List[Dict[str, Any]] = []
        for record in df.to_dict(orient="records"):
            result = self._validate_row(record)
            if result:
                cleaned.append(result)
        if cleaned:
            return pd.DataFrame(cleaned)
        return pd.DataFrame(columns=df.columns)

    # ------------------------------------------------------------------
    def profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return basic profiling statistics for ``df``."""
        df = UnicodeProcessor.sanitize_dataframe(df)
        profile: Dict[str, Any] = {}
        for col in df.columns:
            series = df[col]
            stats: Dict[str, Any] = {
                "dtype": str(series.dtype),
                "count": int(series.count()),
                "missing": int(series.isnull().sum()),
            }
            if pd.api.types.is_numeric_dtype(series):
                stats.update(
                    mean=float(series.mean()),
                    std=float(series.std(ddof=0)),
                    min=float(series.min()),
                    max=float(series.max()),
                )
            else:
                stats["unique"] = int(series.nunique())
            profile[col] = stats
        return profile

    # ------------------------------------------------------------------
    def detect_outliers(
        self,
        df: pd.DataFrame,
        method: str = "zscore",
        *,
        threshold: float = 3.0,
        contamination: float = 0.01,
    ) -> pd.Series:
        """Return boolean mask of outliers using ``method``."""
        numeric = df.select_dtypes(include="number").fillna(0)
        if numeric.empty:
            return pd.Series([False] * len(df), index=df.index)

        if method == "iqr":
            q1 = numeric.quantile(0.25)
            q3 = numeric.quantile(0.75)
            iqr = q3 - q1
            mask = (numeric < (q1 - 1.5 * iqr)) | (numeric > (q3 + 1.5 * iqr))
            return mask.any(axis=1)

        if method == "isolation_forest":
            if IsolationForest is None:
                raise ImportError("scikit-learn is required for IsolationForest")
            model = IsolationForest(
                contamination=contamination, random_state=42
            )
            labels = model.fit_predict(numeric)
            return pd.Series(labels == -1, index=df.index)

        # Default to z-score
        zscores = (numeric - numeric.mean()).abs() / numeric.std(ddof=0)
        mask = zscores > threshold
        return mask.any(axis=1)

    # ------------------------------------------------------------------
    def impute_missing(
        self,
        df: pd.DataFrame,
        *,
        strategy: str = "mean",
        constant: Any | None = None,
    ) -> pd.DataFrame:
        """Return ``df`` with missing values imputed."""
        result = df.copy()
        for col in result.columns:
            if result[col].isnull().any():
                if strategy == "median" and pd.api.types.is_numeric_dtype(result[col]):
                    result[col] = result[col].fillna(result[col].median())
                elif strategy == "mode":
                    mode = result[col].mode().iloc[0]
                    result[col] = result[col].fillna(mode)
                elif strategy == "constant":
                    result[col] = result[col].fillna(constant)
                else:  # mean
                    if pd.api.types.is_numeric_dtype(result[col]):
                        result[col] = result[col].fillna(result[col].mean())
                    else:
                        result[col] = result[col].fillna(constant)
        return result

    # ------------------------------------------------------------------
    def monitor_drift(
        self, current: pd.DataFrame, baseline: pd.DataFrame
    ) -> List[DriftResult]:
        """Compare ``current`` to ``baseline`` and return drift results."""
        results: List[DriftResult] = []
        common = list(set(current.columns) & set(baseline.columns))
        for col in common:
            c = current[col].dropna()
            b = baseline[col].dropna()
            if c.empty or b.empty:
                continue
            if scipy_stats and pd.api.types.is_numeric_dtype(c):
                stat, p = scipy_stats.ks_2samp(c, b)
            else:
                stat = float(abs(c.mean() - b.mean())) if pd.api.types.is_numeric_dtype(c) else 0.0
                p = 0.0
            results.append(DriftResult(col, float(stat), float(p)))
        return results

    # ------------------------------------------------------------------
    def process_batch(self, df: pd.DataFrame) -> DataQualityMetrics:
        """Validate, profile and emit quality metrics for batch ``df``."""
        valid = self.validate_schema(df)
        profile = self.profile(valid)
        outliers = self.detect_outliers(valid)
        metrics = DataQualityMetrics(
            missing_ratio=float(valid.isnull().sum().sum() / valid.size)
            if valid.size
            else 0.0,
            outlier_ratio=float(outliers.mean()),
            schema_violations=len(df) - len(valid),
        )
        self.history.append(metrics)
        self.monitor.emit(metrics)
        logger.debug("Data profile: %s", profile)
        return metrics

    # ------------------------------------------------------------------
    def process_stream(
        self, iterator: Iterable[pd.DataFrame]
    ) -> Generator[DataQualityMetrics, None, None]:
        """Process streaming dataframe chunks."""
        for chunk in iterator:
            yield self.process_batch(chunk)

    # ------------------------------------------------------------------
    def get_dashboard(self) -> Dict[str, Any]:
        """Return dashboard data summarizing recent metrics."""
        return {
            "records": [m.__dict__ for m in self.history[-100:]],
            "count": len(self.history),
        }


__all__ = ["DataQualityFramework", "AccessEventModel", "DriftResult"]
