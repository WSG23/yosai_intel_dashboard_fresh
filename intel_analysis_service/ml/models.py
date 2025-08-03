"""Context-aware models for anomaly detection and risk scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

import pandas as pd


@dataclass
class AnomalyDetector:
    """Simple anomaly detector using dynamic, seasonally-adjusted thresholds.

    The detector computes a per-month mean and standard deviation and flags
    values exceeding ``mean + factor * std``.  A global mean/std is kept as a
    fallback for unseen months.
    """

    factor: float = 3.0
    thresholds: Dict[int, float] | None = None
    global_mean: float | None = None
    global_std: float | None = None

    def fit(self, df: pd.DataFrame, value_col: str = "value", timestamp_col: str = "timestamp") -> "AnomalyDetector":
        if value_col not in df or timestamp_col not in df:
            raise KeyError("DataFrame must contain value and timestamp columns")
        ts = pd.to_datetime(df[timestamp_col])
        values = df[value_col]
        self.global_mean = float(values.mean())
        self.global_std = float(values.std(ddof=0) or 1e-9)
        grouped = df.groupby(ts.dt.month)[value_col]
        self.thresholds = {
            month: float(g.mean() + self.factor * g.std(ddof=0))
            for month, g in grouped
        }
        return self

    def predict(self, df: pd.DataFrame, value_col: str = "value", timestamp_col: str = "timestamp") -> pd.DataFrame:
        if self.thresholds is None:
            raise RuntimeError("Model must be fitted before prediction")
        ts = pd.to_datetime(df[timestamp_col])
        season = ts.dt.month
        default = (self.global_mean or 0.0) + self.factor * (self.global_std or 1.0)
        thresholds = season.map(self.thresholds).fillna(default)
        values = df[value_col]
        anomalies = values > thresholds
        return pd.DataFrame({
            timestamp_col: ts,
            value_col: values,
            "threshold": thresholds,
            "is_anomaly": anomalies,
        })


@dataclass
class RiskScorer:
    """Risk scoring model with seasonal thresholds."""

    weights: Dict[str, float]
    quantile: float = 0.95
    thresholds: Dict[int, float] | None = None

    def fit(self, df: pd.DataFrame, timestamp_col: str = "timestamp") -> "RiskScorer":
        if timestamp_col not in df:
            raise KeyError("DataFrame must contain timestamp column")
        ts = pd.to_datetime(df[timestamp_col])
        scores = self._score_features(df)
        grouped = scores.groupby(ts.dt.month)
        self.thresholds = {month: float(g.quantile(self.quantile)) for month, g in grouped}
        return self

    def _score_features(self, df: pd.DataFrame) -> pd.Series:
        missing = set(self.weights) - set(df)
        if missing:
            raise KeyError(f"Missing features for scoring: {missing}")
        score = pd.Series(0.0, index=df.index)
        for feature, weight in self.weights.items():
            score += df[feature] * weight
        return score

    def score(self, df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
        if self.thresholds is None:
            raise RuntimeError("Model must be fitted before scoring")
        ts = pd.to_datetime(df[timestamp_col])
        scores = self._score_features(df)
        season = ts.dt.month
        default_threshold = pd.Series(self.thresholds.values()).mean()
        thresholds = season.map(self.thresholds).fillna(default_threshold)
        risk = scores > thresholds
        return pd.DataFrame({
            timestamp_col: ts,
            "score": scores,
            "threshold": thresholds,
            "is_risky": risk,
        })
