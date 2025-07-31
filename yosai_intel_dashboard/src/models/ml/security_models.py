from __future__ import annotations

"""Training utilities for core ML models."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Tuple

import joblib
import numpy as np
import pandas as pd

from analytics.feature_extraction import extract_event_features
from monitoring.model_performance_monitor import (
    ModelMetrics,
    get_model_performance_monitor,
)
from yosai_intel_dashboard.src.utils.hashing import hash_dataframe
from yosai_intel_dashboard.src.utils.sklearn_compat import optional_import

from .model_registry import ModelRegistry

IsolationForest = optional_import("sklearn.ensemble.IsolationForest")
DBSCAN = optional_import("sklearn.cluster.DBSCAN")
StandardScaler = optional_import("sklearn.preprocessing.StandardScaler")
SGDClassifier = optional_import("sklearn.linear_model.SGDClassifier")
XGBClassifier = optional_import("xgboost.XGBClassifier")
keras = optional_import("tensorflow.keras")


if IsolationForest is None:  # pragma: no cover - fallback definitions

    class IsolationForest:  # type: ignore
        def __init__(self, *a: Any, **k: Any) -> None:
            raise ImportError("scikit-learn is required for IsolationForest")


if DBSCAN is None:  # pragma: no cover - fallback definitions

    class DBSCAN:  # type: ignore
        def __init__(self, *a: Any, **k: Any) -> None:
            raise ImportError("scikit-learn is required for DBSCAN")


if StandardScaler is None:  # pragma: no cover - fallback definitions

    class StandardScaler:  # type: ignore
        def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
            return X

        def transform(self, X: pd.DataFrame) -> pd.DataFrame:
            return X


if SGDClassifier is None:  # pragma: no cover - fallback definitions

    class SGDClassifier:  # type: ignore
        def __init__(self, *a: Any, **k: Any) -> None:
            raise ImportError("scikit-learn is required for SGDClassifier")


if XGBClassifier is None:  # pragma: no cover - fallback definitions

    class XGBClassifier:  # type: ignore
        def __init__(self, *a: Any, **k: Any) -> None:
            raise ImportError("xgboost is required for XGBClassifier")


if keras is None:  # pragma: no cover - fallback definitions

    class keras:  # type: ignore
        class Sequential:
            def __init__(self, *a: Any, **k: Any) -> None:
                raise ImportError("tensorflow is required for LSTM models")

        class layers:
            LSTM = object
            Dense = object

        class optimizers:
            Adam = object


@dataclass
class TrainResult:
    name: str
    model: Any
    scaler: Any | None
    metrics: dict[str, float]


# ---------------------------------------------------------------------------
def train_access_anomaly_iforest(
    df: pd.DataFrame,
    *,
    contamination: float = 0.1,
    model_registry: ModelRegistry | None = None,
    model_name: str = "access-anomaly-iso",
) -> TrainResult:
    """Train an Isolation Forest anomaly detector for access patterns."""
    features = extract_event_features(df)
    data_cols = [
        "hour",
        "day_of_week",
        "is_weekend",
        "is_after_hours",
        "access_granted",
    ]
    scaler = StandardScaler()
    X = scaler.fit_transform(features[data_cols])
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(X)
    labels = model.predict(X)
    outlier_rate = float((labels == -1).mean())
    metrics = {"outlier_rate": outlier_rate}
    if model_registry:
        _register_model(model_registry, model_name, (model, scaler), metrics, df)
    return TrainResult(model_name, model, scaler, metrics)


# ---------------------------------------------------------------------------
def train_risk_scoring_xgboost(
    df: pd.DataFrame,
    *,
    target_column: str = "risk_label",
    model_registry: ModelRegistry | None = None,
    model_name: str = "risk-score-xgb",
) -> TrainResult:
    """Train an XGBoost classifier for security event risk scoring."""
    if XGBClassifier is None:
        raise ImportError("xgboost is not available")
    if target_column not in df:
        raise ValueError(f"target column '{target_column}' missing")
    features = extract_event_features(df.drop(columns=[target_column]))
    numeric = features.select_dtypes(include=["number", "bool"]).fillna(0)
    scaler = StandardScaler()
    X = scaler.fit_transform(numeric)
    y = df[target_column]
    model = XGBClassifier(
        random_state=42, use_label_encoder=False, eval_metric="logloss"
    )
    model.fit(X, y)
    preds = model.predict(X)
    accuracy = float((preds == y).mean())
    metrics = {"accuracy": accuracy}
    if model_registry:
        _register_model(model_registry, model_name, (model, scaler), metrics, df)
    return TrainResult(model_name, model, scaler, metrics)


# ---------------------------------------------------------------------------
def train_predictive_maintenance_lstm(
    df: pd.DataFrame,
    *,
    sequence_length: int = 10,
    epochs: int = 1,
    model_registry: ModelRegistry | None = None,
    model_name: str = "door-maintenance-lstm",
) -> TrainResult:
    """Train a simple LSTM for door predictive maintenance."""
    if keras is None:
        raise ImportError("tensorflow is not available")

    if "sensor_value" not in df:
        raise ValueError("df must contain 'sensor_value' column")

    df_sorted = df.sort_values("timestamp")
    values = df_sorted["sensor_value"].astype("float32").values
    if len(values) <= sequence_length:
        raise ValueError("not enough data for LSTM training")
    X, y = [], []
    for i in range(len(values) - sequence_length):
        X.append(values[i : i + sequence_length])
        y.append(values[i + sequence_length])
    X = np.array(X).reshape(-1, sequence_length, 1)
    y = np.array(y)

    model = keras.Sequential(
        [
            keras.layers.LSTM(32, input_shape=(sequence_length, 1)),
            keras.layers.Dense(1),
        ]
    )
    model.compile(optimizer=keras.optimizers.Adam(), loss="mse")
    history = model.fit(X, y, epochs=epochs, batch_size=32, verbose=0)
    loss = float(history.history.get("loss", [0.0])[-1])
    metrics = {"loss": loss}
    if model_registry:
        _register_model(model_registry, model_name, model, metrics, df)
    return TrainResult(model_name, model, None, metrics)


# ---------------------------------------------------------------------------
def train_user_clustering_dbscan(
    df: pd.DataFrame,
    *,
    eps: float = 0.5,
    min_samples: int = 5,
    model_registry: ModelRegistry | None = None,
    model_name: str = "user-cluster-dbscan",
) -> TrainResult:
    """Train a DBSCAN model for user behavior clustering."""
    features = extract_event_features(df)
    scaler = StandardScaler()
    X = scaler.fit_transform(
        features[["hour", "day_of_week", "user_event_count", "door_event_count"]]
    )
    model = DBSCAN(eps=eps, min_samples=min_samples)
    labels = model.fit_predict(X)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    metrics = {"clusters": float(n_clusters)}
    if model_registry:
        _register_model(model_registry, model_name, (model, scaler), metrics, df)
    return TrainResult(model_name, model, scaler, metrics)


# ---------------------------------------------------------------------------
def train_online_threat_detector(
    df: pd.DataFrame,
    *,
    classes: list[int] | None = None,
    model_registry: ModelRegistry | None = None,
    model_name: str = "threat-detector-online",
) -> TrainResult:
    """Train an online learning model using ``SGDClassifier``."""
    if SGDClassifier is None:
        raise ImportError("scikit-learn is required for SGDClassifier")
    if classes is None:
        if "label" not in df:
            raise ValueError("df must contain 'label' column for training")
        classes = sorted(df["label"].unique())

    features = extract_event_features(df.drop(columns=["label"]))
    numeric = features.select_dtypes(include=["number", "bool"]).fillna(0)
    scaler = StandardScaler()
    X = scaler.fit_transform(numeric)
    y = df["label"].values

    model = SGDClassifier(random_state=42)
    for i in range(len(X)):
        model.partial_fit(X[i : i + 1], y[i : i + 1], classes=classes)
    preds = model.predict(X)
    accuracy = float((preds == y).mean())
    metrics = {"accuracy": accuracy}
    if model_registry:
        _register_model(model_registry, model_name, (model, scaler), metrics, df)
    return TrainResult(model_name, model, scaler, metrics)


# ---------------------------------------------------------------------------
def _register_model(
    registry: ModelRegistry,
    name: str,
    model_obj: Any,
    metrics: dict[str, float],
    df: pd.DataFrame,
) -> None:
    monitor = get_model_performance_monitor()
    monitor.log_metrics(
        ModelMetrics(
            accuracy=metrics.get("accuracy", 0.0),
            precision=metrics.get("precision", 0.0),
            recall=metrics.get("recall", 0.0),
        )
    )
    dataset_hash = hash_dataframe(df)
    with Path(f"{name}.joblib").open("wb") as fh:
        joblib.dump(model_obj, fh)
    record = registry.register_model(name, f"{name}.joblib", metrics, dataset_hash)
    registry.set_active_version(name, record.version)


__all__ = [
    "train_access_anomaly_iforest",
    "train_risk_scoring_xgboost",
    "train_predictive_maintenance_lstm",
    "train_user_clustering_dbscan",
    "train_online_threat_detector",
    "TrainResult",
]
