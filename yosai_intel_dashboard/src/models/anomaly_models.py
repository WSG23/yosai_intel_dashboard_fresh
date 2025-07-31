from __future__ import annotations

import numpy as np
import pandas as pd

from yosai_intel_dashboard.src.utils.sklearn_compat import optional_import

DBSCAN = optional_import("sklearn.cluster.DBSCAN")
MLPRegressor = optional_import("sklearn.neural_network.MLPRegressor")
StandardScaler = optional_import("sklearn.preprocessing.StandardScaler")

if DBSCAN is None:  # pragma: no cover - fallback definitions

    class DBSCAN:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("scikit-learn is required for DBSCAN")


if MLPRegressor is None:  # pragma: no cover - fallback definitions

    class MLPRegressor:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("scikit-learn is required for MLPRegressor")


if StandardScaler is None:  # pragma: no cover - fallback definitions

    class StandardScaler:  # type: ignore
        def fit_transform(self, X):
            return X

        def transform(self, X):
            return X


__all__ = [
    "train_dbscan_model",
    "train_autoencoder_model",
    "autoencoder_reconstruction_error",
]

_FEATURES = ["hour", "day_of_week", "is_weekend", "is_after_hours", "access_granted"]


def _extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return feature subset used for model training."""
    return df[_FEATURES].copy(deep=False)


def train_dbscan_model(
    df: pd.DataFrame,
    eps: float = 0.5,
    min_samples: int = 5,
) -> tuple[DBSCAN, StandardScaler]:
    """Train a DBSCAN clustering model."""
    features = _extract_features(df)
    scaler = StandardScaler()
    data = scaler.fit_transform(features)
    model = DBSCAN(eps=eps, min_samples=min_samples)
    model.fit(data)
    return model, scaler


def train_autoencoder_model(
    df: pd.DataFrame,
    hidden_layer_sizes: tuple[int, ...] = (8, 4, 8),
    max_iter: int = 200,
) -> tuple[MLPRegressor, StandardScaler]:
    """Train an autoencoder using ``MLPRegressor``."""
    features = _extract_features(df)
    scaler = StandardScaler()
    data = scaler.fit_transform(features)
    model = MLPRegressor(
        hidden_layer_sizes=hidden_layer_sizes,
        random_state=42,
        max_iter=max_iter,
    )
    model.fit(data, data)
    return model, scaler


def autoencoder_reconstruction_error(
    df: pd.DataFrame, model: MLPRegressor, scaler: StandardScaler
) -> np.ndarray:
    """Compute reconstruction error for each row."""
    features = _extract_features(df)
    data = scaler.transform(features)
    reconstructed = model.predict(data)
    if reconstructed.ndim == 1:
        reconstructed = reconstructed.reshape(-1, 1)
    return np.mean((data - reconstructed) ** 2, axis=1)
