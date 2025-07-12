from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

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
