"""Train core security models and register them via ``ModelRegistry``."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from yosai_intel_dashboard.models.ml import (
    ModelRegistry,
    train_access_anomaly_iforest,
    train_online_threat_detector,
    train_predictive_maintenance_lstm,
    train_risk_scoring_xgboost,
    train_user_clustering_dbscan,
)

LOG = logging.getLogger(__name__)

DEFAULT_DB_URL = "sqlite:///model_registry.db"
DEFAULT_BUCKET = "local-models"
DEFAULT_MLFLOW = None


def load_data(path: Path) -> pd.DataFrame:
    LOG.info("Loading data from %s", path)
    return pd.read_csv(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train security ML models")
    parser.add_argument("data", type=Path, help="CSV file with training data")
    parser.add_argument("--registry-db", default=DEFAULT_DB_URL)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--mlflow-uri", default=DEFAULT_MLFLOW)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    df = load_data(args.data)
    registry = ModelRegistry(args.registry_db, args.bucket, mlflow_uri=args.mlflow_uri)

    results = [
        train_access_anomaly_iforest(df, model_registry=registry),
        train_risk_scoring_xgboost(df, model_registry=registry),
    ]

    # LSTM and online models require specific columns; wrap in try/except
    try:
        results.append(train_predictive_maintenance_lstm(df, model_registry=registry))
    except Exception as exc:  # pragma: no cover - missing data
        LOG.warning("Skipping LSTM training: %s", exc)

    try:
        results.append(train_user_clustering_dbscan(df, model_registry=registry))
    except Exception as exc:  # pragma: no cover - fallback
        LOG.warning("Skipping DBSCAN training: %s", exc)

    try:
        results.append(train_online_threat_detector(df, model_registry=registry))
    except Exception as exc:  # pragma: no cover - fallback
        LOG.warning("Skipping online detector training: %s", exc)

    for res in results:
        LOG.info("Registered %s with metrics %s", res.name, res.metrics)

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
