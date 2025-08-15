from __future__ import annotations

import io
import json
import pickle
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


@dataclass
class ModelMetadata:
    """Metadata stored for each persisted model."""

    version: str
    timestamp: str
    parameters: Dict[str, Any]
    checksum: str


ALLOWED_CLASSES: Iterable[Tuple[str, str]] = (
    ("intel_analysis_service.ml.models", "AnomalyDetector"),
    ("intel_analysis_service.ml.models", "RiskScorer"),
)


class _RestrictedUnpickler(pickle.Unpickler):
    """Unpickler that only allows a predefined set of classes."""

    def find_class(self, module: str, name: str) -> Any:  # pragma: no cover - small wrapper
        if (module, name) in ALLOWED_CLASSES:
            __import__(module)
            return getattr(sys.modules[module], name)
        raise pickle.UnpicklingError(f"Global '{module}.{name}' is forbidden")


class ModelRegistry:
    """Simple on-disk registry for storing and loading model artifacts."""

    def __init__(self, base_path: str | Path = "models") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _model_dir(self, name: str, version: str) -> Path:
        return self.base_path / name / version

    def save_model(
        self,
        name: str,
        model: Any,
        parameters: Dict[str, Any],
        version: str | None = None,
    ) -> ModelMetadata:
        """Persist *model* under *name* and return its metadata."""

        version = version or datetime.utcnow().strftime("%Y%m%d%H%M%S")
        data = pickle.dumps(model)
        checksum = sha256(data).hexdigest()
        metadata = ModelMetadata(
            version=version,
            timestamp=datetime.utcnow().isoformat(),
            parameters=parameters,
            checksum=checksum,
        )
        model_dir = self._model_dir(name, version)
        model_dir.mkdir(parents=True, exist_ok=True)
        with open(model_dir / "model.pkl", "wb") as fh:
            fh.write(data)
        with open(model_dir / "metadata.json", "w") as fh:
            json.dump(asdict(metadata), fh)
        return metadata

    def load_model(self, name: str, version: str) -> Tuple[Any, ModelMetadata]:
        """Load *name* model for *version* returning model and metadata."""

        model_dir = self._model_dir(name, version)
        with open(model_dir / "metadata.json") as fh:
            metadata = ModelMetadata(**json.load(fh))
        with open(model_dir / "model.pkl", "rb") as fh:
            data = fh.read()
        if sha256(data).hexdigest() != metadata.checksum:
            raise ValueError("Model checksum mismatch")
        model = _RestrictedUnpickler(io.BytesIO(data)).load()
        return model, metadata


__all__ = ["ModelRegistry", "ModelMetadata"]
