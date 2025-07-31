"""Simple A/B testing wrapper for ML models."""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import joblib

from yosai_intel_dashboard.models.ml import ModelRegistry


class ModelABTester:
    """Route predictions across model versions based on configured weights."""

    def __init__(
        self,
        model_name: str,
        registry: ModelRegistry,
        *,
        weights: Optional[Dict[str, float]] = None,
        weights_file: str = "ab_weights.json",
        model_dir: str = "ab_models",
    ) -> None:
        self.model_name = model_name
        self.registry = registry
        self.weights_file = Path(weights_file)
        self.model_dir = Path(model_dir)
        self.logger = logging.getLogger(__name__)
        self.weights: Dict[str, float] = weights or self._load_weights()
        self.models: Dict[str, Any] = {}
        if self.weights:
            self._load_models()

    # ------------------------------------------------------------------
    def _load_weights(self) -> Dict[str, float]:
        if self.weights_file.exists():
            try:
                with self.weights_file.open() as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    return {str(k): float(v) for k, v in data.items()}
            except Exception as exc:  # pragma: no cover - best effort
                self.logger.warning("Failed to load weights: %s", exc)
        return {}

    def _save_weights(self) -> None:
        try:
            with self.weights_file.open("w") as fh:
                json.dump(self.weights, fh)
        except Exception as exc:  # pragma: no cover - best effort
            self.logger.error("Failed to save weights: %s", exc)

    def _load_models(self) -> None:
        self.models.clear()
        for version in self.weights:
            record = self.registry.get_model(self.model_name, version=version)
            if record is None:
                self.logger.warning(
                    "Model %s version %s not found in registry",
                    self.model_name,
                    version,
                )
                continue
            self.model_dir.mkdir(parents=True, exist_ok=True)
            local_path = self.model_dir / f"{self.model_name}_{version}.bin"
            if not local_path.exists():
                try:
                    self.registry.download_artifact(record.storage_uri, str(local_path))
                except Exception as exc:  # pragma: no cover - network failures
                    self.logger.error(
                        "Failed to download model %s:%s - %s",
                        self.model_name,
                        version,
                        exc,
                    )
                    continue
            try:
                model = joblib.load(local_path)
                self.models[version] = model
            except Exception as exc:  # pragma: no cover - invalid files
                self.logger.error(
                    "Failed to load model artifact %s - %s", local_path, exc
                )

    # ------------------------------------------------------------------
    def set_weights(self, weights: Dict[str, float]) -> None:
        """Update traffic weights and reload models."""
        self.weights = {str(k): float(v) for k, v in weights.items()}
        self._save_weights()
        self._load_models()

    # ------------------------------------------------------------------
    def _choose_version(self) -> str:
        versions = list(self.weights.keys())
        probs = [self.weights[v] for v in versions]
        total = sum(probs)
        if total <= 0:
            raise RuntimeError("Invalid weights: sum must be > 0")
        return random.choices(versions, weights=probs, k=1)[0]

    def predict(self, data: Iterable[Any]) -> Any:
        """Predict using one of the loaded model versions."""
        if not self.weights:
            raise RuntimeError("No traffic weights configured")
        version = self._choose_version()
        model = self.models.get(version)
        if model is None:
            raise RuntimeError(f"Model version {version} not loaded")
        result = model.predict(data)
        self.logger.info("ab_test_prediction", extra={"version": version})
        return result


__all__ = ["ModelABTester"]
