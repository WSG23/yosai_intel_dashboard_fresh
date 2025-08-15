from __future__ import annotations

import json
import pickle
import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple


@dataclass
class ModelMetadata:
    """Metadata stored for each persisted model."""

    version: str
    timestamp: str
    parameters: Dict[str, Any]
    sha256: str


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
        model_dir = self._model_dir(name, version)
        model_dir.mkdir(parents=True, exist_ok=True)

        data = pickle.dumps(model)
        sha256 = hashlib.sha256(data).hexdigest()
        metadata = ModelMetadata(
            version=version,
            timestamp=datetime.utcnow().isoformat(),
            parameters=parameters,
            sha256=sha256,
        )

        with open(model_dir / "model.pkl", "wb") as fh:
            fh.write(data)
        with open(model_dir / "metadata.json", "w") as fh:
            json.dump(asdict(metadata), fh)
        return metadata

    def load_model(self, name: str, version: str) -> Tuple[Any, ModelMetadata]:
        """Load *name* model for *version* returning model and metadata."""

        model_dir = self._model_dir(name, version)
        model_file = model_dir / "model.pkl"
        with open(model_file, "rb") as fh:
            data = fh.read()
            file_hash = hashlib.sha256(data).hexdigest()
        with open(model_dir / "metadata.json") as fh:
            metadata = ModelMetadata(**json.load(fh))
        if file_hash != metadata.sha256:
            raise ValueError("Model artifact hash mismatch")
        model = pickle.loads(data)
        return model, metadata


__all__ = ["ModelRegistry", "ModelMetadata"]
