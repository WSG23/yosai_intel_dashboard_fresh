#!/usr/bin/env python3
"""Model explainability utilities.

This service exposes helper methods for computing SHAP and LIME
explanations as well as basic fairness metrics.  It is designed to
work with any scikit-learn compatible estimator and can generate
explanations on demand.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable

import numpy as np
import pandas as pd
import shap
from fairlearn.metrics import MetricFrame, selection_rate
from lime.lime_tabular import LimeTabularExplainer
from sklearn.base import BaseEstimator
from sklearn.metrics import accuracy_score

logger = logging.getLogger(__name__)


@dataclass
class RegisteredModel:
    """Internal record for a registered model."""

    model: BaseEstimator
    background: pd.DataFrame
    explainer: shap.Explainer


class ExplainabilityService:
    """Provide real-time model explainability features."""

    def __init__(self) -> None:
        self._models: dict[str, RegisteredModel] = {}

    # ------------------------------------------------------------------
    def register_model(
        self, name: str, model: BaseEstimator, *, background_data: pd.DataFrame
    ) -> None:
        """Register ``model`` with optional background data for SHAP."""
        explainer = shap.Explainer(model, background_data)
        self._models[name] = RegisteredModel(model, background_data, explainer)
        logger.info("registered model %s", name)

    def _get(self, name: str) -> RegisteredModel:
        if name not in self._models:
            raise KeyError(f"model {name} not registered")
        return self._models[name]

    # ------------------------------------------------------------------
    def shap_values(self, name: str, data: pd.DataFrame) -> np.ndarray:
        """Return SHAP values for ``data`` using the registered model."""
        record = self._get(name)
        shap_values = record.explainer(data)
        return shap_values.values

    def lime_explanation(
        self, name: str, data: pd.DataFrame, row: int
    ) -> Dict[str, float]:
        """Generate a LIME explanation for ``data.iloc[row]``."""
        record = self._get(name)
        instance = data.iloc[row]
        explainer = LimeTabularExplainer(
            record.background.to_numpy(),
            feature_names=list(data.columns),
            discretize_continuous=True,
        )
        exp = explainer.explain_instance(
            instance.to_numpy(),
            record.model.predict_proba,
            num_features=min(10, data.shape[1]),
        )
        return dict(exp.as_list())

    def feature_importance(self, name: str, data: pd.DataFrame) -> Dict[str, float]:
        """Return global feature importance for ``model``."""
        record = self._get(name)
        model = record.model
        if hasattr(model, "feature_importances_"):
            scores = np.asarray(model.feature_importances_)
        elif hasattr(model, "coef_"):
            scores = np.abs(np.asarray(model.coef_)).reshape(-1)
        else:
            scores = np.abs(self.shap_values(name, data)).mean(axis=0)
        return dict(zip(data.columns, scores))

    def counterfactual(
        self,
        name: str,
        data: pd.DataFrame,
        row: int,
        desired: Iterable[float] | float,
        *,
        max_iter: int = 200,
        step: float = 0.1,
    ) -> Dict[str, Any]:
        """Generate a simple counterfactual example.

        This uses a naive gradient-free search that nudges features until the
        prediction is close to ``desired``.  It works for demonstration
        purposes but is not optimized for performance.
        """
        record = self._get(name)
        target = float(np.squeeze(desired))
        x = data.iloc[row].to_numpy().astype(float)
        current = float(record.model.predict(x.reshape(1, -1))[0])
        for _ in range(max_iter):
            if abs(current - target) < 0.01:
                break
            grads = record.explainer.shap_values(x.reshape(1, -1))[0]
            direction = np.sign(target - current) * np.sign(grads)
            x = x + step * direction
            current = float(record.model.predict(x.reshape(1, -1))[0])
        return {"original": data.iloc[row].to_dict(), "counterfactual": x.tolist()}

    def visualize_model(self, name: str, data: pd.DataFrame, path: Path) -> Path:
        """Save a SHAP summary plot to ``path``."""
        record = self._get(name)
        shap_values = record.explainer(data)
        shap.summary_plot(shap_values, data, show=False)
        path.parent.mkdir(parents=True, exist_ok=True)
        shap.plots.save(path)
        return path

    def bias_metrics(
        self,
        y_true: Iterable[Any],
        y_pred: Iterable[Any],
        sensitive_features: Iterable[Any],
    ) -> Dict[str, Any]:
        """Return basic fairness metrics for the predictions."""
        frame = MetricFrame(
            metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
            y_true=list(y_true),
            y_pred=list(y_pred),
            sensitive_features=list(sensitive_features),
        )
        return {
            "overall": frame.overall.to_dict(),
            "by_group": frame.by_group.to_dict(),
        }

    def natural_language_explanation(
        self, feature_weights: Dict[str, float], prediction: Any
    ) -> str:
        """Generate a simple natural language summary of the prediction."""
        sorted_feats = sorted(
            feature_weights.items(), key=lambda x: abs(x[1]), reverse=True
        )
        top_feats = ", ".join(f"{k} ({v:.2f})" for k, v in sorted_feats[:3])
        return f"Prediction {prediction} was mainly influenced by {top_feats}."


__all__ = ["ExplainabilityService"]
