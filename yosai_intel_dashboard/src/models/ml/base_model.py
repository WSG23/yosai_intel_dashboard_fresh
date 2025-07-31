from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
from packaging.version import Version

from core.unicode import clean_unicode_text, contains_surrogates
from monitoring.model_performance_monitor import (
    ModelMetrics,
    get_model_performance_monitor,
)
from yosai_intel_dashboard.src.utils.sklearn_compat import optional_import

# Optional dependencies
shap = optional_import("shap")
lime_tabular = optional_import("lime.lime_tabular.LimeTabularExplainer")
lime_text = optional_import("lime.lime_text.LimeTextExplainer")
torch = optional_import("torch")

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata describing an ML model."""

    name: str
    version: str = "0.1.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    description: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


class BaseModel(ABC):
    """Abstract base class for ML models with monitoring and explainability."""

    def __init__(
        self,
        *,
        metadata: ModelMetadata,
        metrics: Dict[str, float] | None = None,
        device: str | None = None,
    ) -> None:
        self.metadata = metadata
        self.metrics = metrics or {}
        self.model: Any | None = None
        self._predict_lock = threading.Lock()
        if torch is not None:
            chosen = device or ("cuda" if torch.cuda.is_available() else "cpu")
            self.device = torch.device(chosen)
        else:
            self.device = device or "cpu"
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------
    def bump_version(self, improved: bool = False) -> None:
        """Increment the version string."""
        ver = Version(self.metadata.version)
        if improved:
            self.metadata.version = f"{ver.major}.{ver.minor + 1}.0"
        else:
            self.metadata.version = f"{ver.major}.{ver.minor}.{ver.micro + 1}"

    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "created_at": self.metadata.created_at.isoformat(),
            "description": self.metadata.description,
            "metrics": self.metrics,
            **self.metadata.extra,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    # ------------------------------------------------------------------
    def save_checkpoint(self, path: str | Path) -> None:
        """Persist model state and metadata to ``path``."""
        data = {
            "model": self.model,
            "metadata": self.metadata,
            "metrics": self.metrics,
        }
        joblib.dump(data, Path(path))

    def load_checkpoint(self, path: str | Path) -> None:
        """Load model state and metadata from ``path``."""
        data = joblib.load(Path(path))
        self.model = data.get("model")
        self.metadata = data.get("metadata", self.metadata)
        self.metrics = data.get("metrics", self.metrics)

    # ------------------------------------------------------------------
    def log_metrics(self) -> None:
        """Send metrics to the global performance monitor."""
        if not self.metrics:
            return
        monitor = get_model_performance_monitor()
        metrics = ModelMetrics(
            accuracy=float(self.metrics.get("accuracy", 0.0)),
            precision=float(self.metrics.get("precision", 0.0)),
            recall=float(self.metrics.get("recall", 0.0)),
        )
        monitor.log_metrics(metrics)

    # ------------------------------------------------------------------
    def predict(self, data: Any, *, log_prediction: bool | None = None) -> Any:
        """Thread-safe prediction wrapper with optional event logging."""
        prepared = self._sanitize_input(data)
        with self._predict_lock:
            if torch is not None and hasattr(self.model, "to"):
                self.model.to(self.device)
            result = self._predict(prepared)

        if log_prediction is None:
            flag = os.getenv("MODEL_PREDICTION_LOGGING", "0").lower()
            log_prediction = flag in {"1", "true", "yes"}

        if log_prediction:
            monitor = get_model_performance_monitor()
            input_hash = self._hash_input(prepared)
            monitor.log_prediction(input_hash, result, datetime.utcnow())

        return result

    @abstractmethod
    def _predict(self, data: Any) -> Any:
        """Model-specific prediction implementation."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    def _sanitize_input(self, data: Any) -> Any:
        """Recursively sanitize text inputs."""
        if isinstance(data, str):
            if contains_surrogates(data):
                return clean_unicode_text(data)
            return clean_unicode_text(data)
        if isinstance(data, list):
            return [self._sanitize_input(v) for v in data]
        if isinstance(data, dict):
            return {k: self._sanitize_input(v) for k, v in data.items()}
        return data

    def _hash_input(self, data: Any) -> str:
        """Return a stable SHA256 hash for ``data``."""
        try:
            normalized = json.dumps(data, sort_keys=True, default=str)
        except Exception:
            normalized = str(data)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    def explain_shap(self, data: Any) -> Any:
        """Return SHAP explanations for ``data`` if ``shap`` is available."""
        if shap is None:
            raise ImportError("shap is not available")
        with self._predict_lock:
            explainer = shap.Explainer(self.model)
            return explainer(self._sanitize_input(data))

    def explain_lime(self, data: Any, **kwargs: Any) -> Any:
        """Return LIME explanation for ``data`` if ``lime`` is available."""
        if lime_tabular is None:
            raise ImportError("lime is not available")
        training = self._get_training_data()
        explainer = lime_tabular(training_data=training, **kwargs)
        with self._predict_lock:
            return explainer.explain_instance(
                self._sanitize_input(data),
                lambda x: self._predict(x),
            )

    def _get_training_data(self) -> Any:
        """Return data used for training if available."""
        return getattr(self, "training_data", None)

    # ------------------------------------------------------------------
    def set_device(self, device: str) -> None:
        """Move the model to ``device`` if supported."""
        if torch is not None:
            self.device = torch.device(device)
            if self.model is not None and hasattr(self.model, "to"):
                self.model.to(self.device)
        else:
            self.device = device


__all__ = ["ModelMetadata", "BaseModel"]
