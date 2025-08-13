#!/usr/bin/env python3
"""Train anomaly detection models and register them.

This script loads raw access events, prepares the dataset for
machine learning and trains DBSCAN and autoencoder models.
Each trained model is saved locally and registered via
:class:`models.ml.ModelRegistry`.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

from analytics.anomaly_detection.data_prep import prepare_anomaly_data
from yosai_intel_dashboard.models.anomaly_models import (
    autoencoder_reconstruction_error,
    train_autoencoder_model,
    train_dbscan_model,
)
from yosai_intel_dashboard.models.ml import ModelRegistry

LOG = logging.getLogger(__name__)


DEFAULT_DB_URL = os.getenv("MODEL_REGISTRY_DB", "sqlite:///model_registry.db")
DEFAULT_BUCKET = os.getenv("MODEL_REGISTRY_BUCKET", "local-models")
DEFAULT_MLFLOW = os.getenv("MLFLOW_URI")


def compute_dataset_hash(df: pd.DataFrame) -> str:
    """Return SHA256 hash of ``df`` serialized as CSV."""
    csv_bytes = df.to_csv(index=False).encode()
    return hashlib.sha256(csv_bytes).hexdigest()


def train_models(
    df: pd.DataFrame, include_iso: bool
) -> list[tuple[str, Any, dict[str, float]]]:
    """Train anomaly models and return metadata tuples."""
    results: list[tuple[str, Any, dict[str, float]]] = []

    dbscan_model, dbscan_scaler = train_dbscan_model(df)
    feature_cols = [
        "hour",
        "day_of_week",
        "is_weekend",
        "is_after_hours",
        "access_granted",
    ]
    features = df[feature_cols]
    labels = getattr(
        dbscan_model,
        "labels_",
        dbscan_model.fit_predict(dbscan_scaler.transform(features)),
    )
    outlier_rate = float((labels == -1).mean())
    results.append(
        (
            "dbscan_anomaly",
            (dbscan_model, dbscan_scaler),
            {"outlier_rate": outlier_rate},
        )
    )

    ae_model, ae_scaler = train_autoencoder_model(df)
    errors = autoencoder_reconstruction_error(df, ae_model, ae_scaler)
    results.append(
        (
            "autoencoder_anomaly",
            (ae_model, ae_scaler),
            {"reconstruction_mse": float(errors.mean())},
        )
    )

    if include_iso:
        iso = IsolationForest(random_state=42, contamination=0.1)
        iso.fit(
            df[
                [
                    "hour",
                    "day_of_week",
                    "is_weekend",
                    "is_after_hours",
                    "access_granted",
                ]
            ]
        )
        scores = -iso.decision_function(
            df[
                [
                    "hour",
                    "day_of_week",
                    "is_weekend",
                    "is_after_hours",
                    "access_granted",
                ]
            ]
        )
        results.append(
            (
                "isolation_forest_anomaly",
                iso,
                {"mean_score": float(scores.mean())},
            )
        )

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train anomaly detection models")
    parser.add_argument("data", type=Path, help="CSV file containing raw events")
    parser.add_argument(
        "--include-iso",
        action="store_true",
        help="Also train an IsolationForest model",
    )
    parser.add_argument(
        "--registry-db",
        default=DEFAULT_DB_URL,
        help="SQLAlchemy database URL for model registry",
    )
    parser.add_argument(
        "--bucket",
        default=DEFAULT_BUCKET,
        help="Bucket name for storing model artifacts",
    )
    parser.add_argument(
        "--mlflow-uri",
        default=DEFAULT_MLFLOW,
        help="Optional MLflow tracking URI",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    LOG.info("Loading events from %s", args.data)
    raw_df = pd.read_csv(args.data)
    df = prepare_anomaly_data(raw_df)

    dataset_hash = compute_dataset_hash(df)
    LOG.info("Dataset contains %s rows", len(df))

    registry = ModelRegistry(args.registry_db, args.bucket, mlflow_uri=args.mlflow_uri)

    models = train_models(df, args.include_iso)
    for name, model_obj, metrics in models:
        LOG.info("Registering %s model", name)
        with Path(f"{name}.joblib").open("wb") as fh:
            joblib.dump(model_obj, fh)
        record = registry.register_model(
            name,
            f"{name}.joblib",
            metrics,
            dataset_hash,
            feature_defs_version=None,
        )
        LOG.info("Registered %s version %s", record.name, record.version)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
