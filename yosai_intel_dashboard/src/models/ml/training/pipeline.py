from __future__ import annotations

"""Automated ML training pipeline utilities."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import numpy as np
import pandas as pd

from yosai_intel_dashboard.src.utils.hashing import hash_dataframe
from yosai_intel_dashboard.src.utils.sklearn_compat import optional_import
from yosai_intel_dashboard.models.ml import ModelRegistry
from yosai_intel_dashboard.models.ml.feature_store import FeastFeatureStore
from yosai_intel_dashboard.models.ml.pipeline_contract import preprocess_events
from yosai_intel_dashboard.models.ml.training.bias import detect_bias

# Optional heavy dependencies
KFold = optional_import("sklearn.model_selection.KFold")
StratifiedKFold = optional_import("sklearn.model_selection.StratifiedKFold")
train_test_split = optional_import("sklearn.model_selection.train_test_split")
BayesSearchCV = optional_import("skopt.BayesSearchCV")
JoblibParallelBackend = optional_import("joblib.parallel_backend")
DaskClient = optional_import("dask.distributed.Client")
DaskLocalCluster = optional_import("dask.distributed.LocalCluster")
mlflow = optional_import("mlflow")

logger = logging.getLogger(__name__)


@dataclass
class ExperimentResult:
    name: str
    metrics: Dict[str, float]
    model_path: Path
    bias_metrics: Dict[str, Any] | None = None


class TrainingPipeline:
    """Automated training pipeline with experiment tracking and tuning."""

    def __init__(
        self,
        registry: ModelRegistry,
        *,
        cv_splits: int = 5,
        scoring: str = "accuracy",
        distributed: bool = False,
        mlflow_uri: str | None = None,
    ) -> None:
        self.registry = registry
        self.cv_splits = cv_splits
        self.scoring = scoring
        self.distributed = distributed
        if mlflow and mlflow_uri:
            mlflow.set_tracking_uri(mlflow_uri)

    # ------------------------------------------------------------------
    def _get_cv(self, y: Iterable[Any]) -> Any:
        if StratifiedKFold and len(set(y)) > 1:
            return StratifiedKFold(
                n_splits=self.cv_splits, shuffle=True, random_state=42
            )
        if KFold:
            return KFold(n_splits=self.cv_splits, shuffle=True, random_state=42)
        raise RuntimeError("scikit-learn is required for cross-validation")

    # ------------------------------------------------------------------
    def _tune_hyperparams(
        self, model: Any, params: Dict[str, Any], X: np.ndarray, y: np.ndarray
    ) -> Any:
        if BayesSearchCV is None:
            logger.warning("Bayesian optimization unavailable; skipping tuning")
            return model.fit(X, y)

        cv = self._get_cv(y)
        search = BayesSearchCV(model, params, cv=cv, scoring=self.scoring, n_jobs=-1)
        search.fit(X, y)
        return search.best_estimator_

    # ------------------------------------------------------------------
    def _train_single(
        self,
        name: str,
        estimator: Any,
        param_space: Dict[str, Any],
        X: np.ndarray,
        y: np.ndarray,
        dataset_hash: str,
    ) -> ExperimentResult:
        client = None
        cluster = None
        try:
            if (
                self.distributed
                and DaskClient
                and DaskLocalCluster
                and JoblibParallelBackend
            ):
                cluster = DaskLocalCluster(n_workers=2, threads_per_worker=2)
                client = DaskClient(cluster)
            if client and JoblibParallelBackend:
                with JoblibParallelBackend("dask"):
                    best_model = self._tune_hyperparams(estimator, param_space, X, y)
            else:
                best_model = self._tune_hyperparams(estimator, param_space, X, y)
        finally:
            if client:
                client.close()
            if cluster:
                cluster.close()

        with Path(f"{name}.joblib").open("wb") as fh:
            optional_import("joblib").dump(best_model, fh)

        metrics = {self.scoring: float(getattr(best_model, self.scoring, 0.0))}
        if mlflow:
            with mlflow.start_run() as run:
                mlflow.log_params(best_model.get_params())
                mlflow.log_metric(self.scoring, metrics[self.scoring])
                mlflow.log_artifact(f"{name}.joblib")
                mlflow.log_text(dataset_hash, "dataset_hash.txt")

        return ExperimentResult(name, metrics, Path(f"{name}.joblib"))

    # ------------------------------------------------------------------
    def run(
        self,
        entity_df: pd.DataFrame,
        target_column: str,
        models: Dict[str, Tuple[Any, Dict[str, Any]]],
        *,
        feature_store: FeastFeatureStore | None = None,
        feature_service: Any | None = None,
        bias_column: str | None = None,
        bias_report: Path | None = None,
    ) -> ExperimentResult:
        """Run hyperparameter tuning and register the best performing model."""
        X, y, df, dataset_hash = self._prepare_data(
            entity_df,
            target_column,
            feature_store=feature_store,
            feature_service=feature_service,
        )

        best_res = self._train_models(models, X, y, dataset_hash)
        self._register_best_model(best_res, dataset_hash)
        self._handle_bias(best_res, df, X, y, bias_column, bias_report)
        return best_res

    # ------------------------------------------------------------------
    def _prepare_data(
        self,
        entity_df: pd.DataFrame,
        target_column: str,
        *,
        feature_store: FeastFeatureStore | None = None,
        feature_service: Any | None = None,
    ) -> tuple[np.ndarray, np.ndarray, pd.DataFrame, str]:
        """Return feature matrix, target vector, processed dataframe and hash."""
        if feature_store:
            if feature_service is None:
                raise ValueError("feature_service required when using feature_store")
            df = feature_store.get_training_dataframe(feature_service, entity_df)
        else:
            df = entity_df

        df = preprocess_events(df)

        if target_column not in df:
            raise ValueError(f"target column '{target_column}' missing")

        dataset_hash = hash_dataframe(df)
        y = df[target_column].values
        feature_df = df.drop(columns=[target_column])
        X = (
            feature_df
            .select_dtypes(include=["number", "bool"])
            .fillna(0)
            .values
        )
        return X, y, df, dataset_hash

    # ------------------------------------------------------------------
    def _train_models(
        self,
        models: Dict[str, Tuple[Any, Dict[str, Any]]],
        X: np.ndarray,
        y: np.ndarray,
        dataset_hash: str,
    ) -> ExperimentResult:
        """Train each candidate model and return the best result."""
        best_res: ExperimentResult | None = None
        for name, (estimator, param_space) in models.items():
            logger.info("Training %s", name)
            res = self._train_single(name, estimator, param_space, X, y, dataset_hash)
            if (
                not best_res
                or res.metrics[self.scoring] > best_res.metrics[self.scoring]
            ):
                best_res = res
        assert best_res is not None
        return best_res

    # ------------------------------------------------------------------
    def _register_best_model(self, best_res: ExperimentResult, dataset_hash: str) -> None:
        """Register the winning model and optionally activate it."""
        active = self.registry.get_model(best_res.name, active_only=True)
        improved = active is None or self.registry._metrics_improved(
            best_res.metrics, active.metrics or {}
        )
        record = self.registry.register_model(
            best_res.name,
            str(best_res.model_path),
            best_res.metrics,
            dataset_hash,
        )
        if improved:
            self.registry.set_active_version(best_res.name, record.version)

    # ------------------------------------------------------------------
    def _handle_bias(
        self,
        best_res: ExperimentResult,
        df: pd.DataFrame,
        X: np.ndarray,
        y: np.ndarray,
        bias_column: str | None,
        bias_report: Path | None,
    ) -> None:
        if bias_column and bias_column in df.columns:
            model = optional_import("joblib").load(best_res.model_path)
            y_pred = model.predict(X)
            bias_metrics = detect_bias(y, y_pred, df[bias_column].values)
            best_res.bias_metrics = bias_metrics
            if bias_report:
                bias_report.write_text(json.dumps(bias_metrics, indent=2))


__all__ = ["TrainingPipeline", "ExperimentResult"]
