from __future__ import annotations

"""Machine learning risk scoring utilities."""

import hashlib
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Tuple

import joblib
import pandas as pd


def optional_import(name: str, fallback: type | None = None) -> Any:
    """Attempt to import ``name`` returning ``fallback`` if unavailable."""
    try:
        if name.startswith("sklearn."):
            parts = name.split(".")
            if len(parts) > 2:
                module_path = ".".join(parts[:-1])
                class_name = parts[-1]
                module = __import__(module_path, fromlist=[class_name])
                return getattr(module, class_name)
            module = __import__(name, fromlist=["*"])
        else:
            module = __import__(name, fromlist=["*"])
        return module
    except Exception as exc:  # pragma: no cover - optional dependency
        import logging

        logging.getLogger(__name__).warning(
            "Optional dependency '%s' unavailable: %s", name, exc
        )
        return fallback


if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from yosai_intel_dashboard.src.core.domain.ml import ModelRegistry
else:  # pragma: no cover - runtime fallback
    ModelRegistry = Any  # type: ignore

LogisticRegression = optional_import("sklearn.linear_model.LogisticRegression")
GradientBoostingClassifier = optional_import(
    "sklearn.ensemble.GradientBoostingClassifier"
)
StandardScaler = optional_import("sklearn.preprocessing.StandardScaler")

if LogisticRegression is None:  # pragma: no cover - fallback definitions

    class LogisticRegression:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("scikit-learn is required for LogisticRegression")


if GradientBoostingClassifier is None:  # pragma: no cover - fallback definitions

    class GradientBoostingClassifier:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("scikit-learn is required for GradientBoostingClassifier")


if StandardScaler is None:  # pragma: no cover - fallback definitions

    class StandardScaler:  # type: ignore
        def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
            return X

        def transform(self, X: pd.DataFrame) -> pd.DataFrame:
            return X


__all__ = ["train_risk_model", "predict_risk_score"]


_TARGET_COLUMNS = ["risk_label", "label", "target"]


def _select_target_column(df: pd.DataFrame) -> str:
    for col in _TARGET_COLUMNS:
        if col in df.columns:
            return col
    raise ValueError("DataFrame must contain a target column")


def train_risk_model(
    df: pd.DataFrame,
    *,
    model_registry: Optional[ModelRegistry] = None,
    model_name: str = "risk-model",
) -> Tuple[Any, Any]:
    """Train a simple risk classification model.

    Parameters
    ----------
    df:
        Training data including a binary target column.
    model_registry:
        Optional model registry used to version the trained model.
    model_name:
        Name under which the model should be registered.

    Returns
    -------
    tuple
        ``(model, scaler)`` pair.
    """

    target_col = _select_target_column(df)
    feature_df = df.drop(columns=[target_col])
    numeric = feature_df.select_dtypes(include=["number", "bool"]).fillna(0)

    scaler = StandardScaler()
    data = scaler.fit_transform(numeric)

    # Use gradient boosting if available, otherwise logistic regression
    if GradientBoostingClassifier is not None:
        model = GradientBoostingClassifier(random_state=42)
    else:
        model = LogisticRegression(max_iter=200)

    model.fit(data, df[target_col])

    if model_registry is not None:
        metrics = {"accuracy": float(model.score(data, df[target_col]))}
        dataset_hash = hashlib.sha256(
            pd.util.hash_pandas_object(df, index=True).values.tobytes()
        ).hexdigest()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "model.joblib"
            joblib.dump({"model": model, "scaler": scaler}, path)
            record = model_registry.register_model(
                model_name,
                str(path),
                metrics,
                dataset_hash,
            )
            model_registry.set_active_version(model_name, record.version)

    return model, scaler


def predict_risk_score(
    model: Any, features: pd.DataFrame | list | tuple | Any, scaler: Any | None = None
) -> Any:
    """Predict risk score or probability for the given features."""

    df = pd.DataFrame(features)
    data = df if scaler is None else scaler.transform(df)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(data)
        if proba.ndim == 2:
            return proba[:, -1]
        return proba
    return model.predict(data)
