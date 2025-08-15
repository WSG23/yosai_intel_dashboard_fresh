"""Context-aware models for anomaly detection and risk scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Protocol

import logging
from opentelemetry import trace
import pandas as pd

from .model_registry import ModelRegistry, ModelMetadata

tracer = trace.get_tracer(__name__)


class DriftDetector(Protocol):
    """Protocol describing drift detection behaviour."""

    def detect(self, values: Iterable[float], thresholds: Iterable[float]) -> bool:
        """Return True if drift is detected for ``values`` vs ``thresholds``."""


@dataclass
class AnomalyDetector:
    """Simple anomaly detector using dynamic, seasonally-adjusted thresholds.

    The detector computes a per-month mean and standard deviation and flags
    values exceeding ``mean + factor * std``.  A global mean/std is kept as a
    fallback for unseen months.
    """

    factor: float = 3.0
    context_weights: Dict[str, float] | None = None
    context_means: Dict[str, float] | None = None
    thresholds: Dict[int, float] | None = None
    global_mean: float | None = None
    global_std: float | None = None
    model_version: str = "1.0"
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))
    drift_detector: DriftDetector | None = None

    def fit(
        self,
        df: pd.DataFrame,
        value_col: str = "value",
        timestamp_col: str = "timestamp",
    ) -> "AnomalyDetector":
        if value_col not in df or timestamp_col not in df:
            raise KeyError("DataFrame must contain value and timestamp columns")
        ts = pd.to_datetime(df[timestamp_col])
        values = df[value_col]
        self.global_mean = float(values.mean())
        self.global_std = float(values.std(ddof=0) or 1e-9)
        grouped = df.groupby(ts.dt.month)[value_col]
        self.thresholds = {
            month: float(g.mean() + self.factor * g.std(ddof=0)) for month, g in grouped
        }

        if self.context_weights:
            self.context_means = {
                col: float(df[col].mean()) for col in self.context_weights if col in df
            }
        else:
            self.context_means = {}
        return self

    def predict(
        self,
        df: pd.DataFrame,
        value_col: str = "value",
        timestamp_col: str = "timestamp",
    ) -> pd.DataFrame:
        if self.thresholds is None:
            raise RuntimeError("Model must be fitted before prediction")
        with tracer.start_as_current_span("anomaly_predict"):
            ts = pd.to_datetime(df[timestamp_col])
            season = ts.dt.month
            default = (self.global_mean or 0.0) + self.factor * (self.global_std or 1.0)
            thresholds = season.map(self.thresholds).fillna(default)

            context = pd.Series(0.0, index=df.index)
            if self.context_weights:
                for col, weight in self.context_weights.items():
                    if col in df:
                        base = (self.context_means or {}).get(col, 0.0)
                        context += (df[col] - base) * weight
            thresholds = thresholds + context

            values = df[value_col]
            anomalies = values > thresholds
            result = pd.DataFrame(
                {
                    timestamp_col: ts,
                    value_col: values,
                    "threshold": thresholds,
                    "is_anomaly": anomalies,
                }
            )
            self.logger.info(
                "model=%s predictions=%s thresholds=%s",
                self.model_version,
                result[value_col].tolist(),
                result["threshold"].tolist(),
            )
            if self.drift_detector:
                drift = self.drift_detector.detect(
                    result[value_col], result["threshold"]
                )
                result["drift_detected"] = drift
            return result

    def save(
        self,
        registry: ModelRegistry,
        name: str = "anomaly_detector",
        version: str | None = None,
    ) -> ModelMetadata:
        """Persist the trained model using *registry* and return its metadata."""

        params = {"factor": self.factor, "context_weights": self.context_weights}
        metadata = registry.save_model(name, self, params, version)
        self.model_version = metadata.version
        return metadata

    @classmethod
    def load(
        cls,
        registry: ModelRegistry,
        version: str,
        name: str = "anomaly_detector",
    ) -> "AnomalyDetector":
        """Load a persisted model from *registry* for *version*."""

        model, _ = registry.load_model(name, version)
        assert isinstance(model, cls)
        return model


@dataclass
class RiskScorer:
    """Risk scoring model with seasonal thresholds."""

    weights: Dict[str, float]
    quantile: float = 0.95
    thresholds: Dict[int, float] | None = None
    model_version: str = "1.0"
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))
    drift_detector: DriftDetector | None = None

    def fit(self, df: pd.DataFrame, timestamp_col: str = "timestamp") -> "RiskScorer":
        if timestamp_col not in df:
            raise KeyError("DataFrame must contain timestamp column")
        ts = pd.to_datetime(df[timestamp_col])
        scores = self._score_features(df)
        grouped = scores.groupby(ts.dt.month)
        self.thresholds = {
            month: float(g.quantile(self.quantile)) for month, g in grouped
        }
        return self

    def _score_features(self, df: pd.DataFrame) -> pd.Series:
        missing = set(self.weights) - set(df)
        if missing:
            raise KeyError(f"Missing features for scoring: {missing}")
        score: pd.Series = pd.Series(0.0, index=df.index)
        for feature, weight in self.weights.items():
            score += df[feature] * weight
        return score

    def score(self, df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
        if self.thresholds is None:
            raise RuntimeError("Model must be fitted before scoring")
        with tracer.start_as_current_span("risk_score"):
            ts = pd.to_datetime(df[timestamp_col])
            scores = self._score_features(df)
            season = ts.dt.month
            default_threshold = pd.Series(self.thresholds.values()).mean()
            thresholds = season.map(self.thresholds).fillna(default_threshold)
            risk = scores > thresholds
            result = pd.DataFrame(
                {
                    timestamp_col: ts,
                    "score": scores,
                    "threshold": thresholds,
                    "is_risky": risk,
                }
            )
            self.logger.info(
                "model=%s predictions=%s thresholds=%s",
                self.model_version,
                result["score"].tolist(),
                result["threshold"].tolist(),
            )
            if self.drift_detector:
                drift = self.drift_detector.detect(result["score"], result["threshold"])
                result["drift_detected"] = drift
            return result

    def save(
        self,
        registry: ModelRegistry,
        name: str = "risk_scorer",
        version: str | None = None,
    ) -> ModelMetadata:
        """Persist the trained model using *registry* and return its metadata."""

        params = {"weights": self.weights, "quantile": self.quantile}
        metadata = registry.save_model(name, self, params, version)
        self.model_version = metadata.version
        return metadata

    @classmethod
    def load(
        cls,
        registry: ModelRegistry,
        version: str,
        name: str = "risk_scorer",
    ) -> "RiskScorer":
        """Load a persisted model from *registry* for *version*."""

        model, _ = registry.load_model(name, version)
        assert isinstance(model, cls)
        return model


def load_anomaly_model(version: str, registry: ModelRegistry | None = None) -> AnomalyDetector:
    """Convenience loader for :class:`AnomalyDetector`."""

    registry = registry or ModelRegistry()
    return AnomalyDetector.load(registry, version)


def load_risk_model(version: str, registry: ModelRegistry | None = None) -> RiskScorer:
    """Convenience loader for :class:`RiskScorer`."""

    registry = registry or ModelRegistry()
    return RiskScorer.load(registry, version)
