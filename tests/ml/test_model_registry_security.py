import json
import pickle
from datetime import datetime
from hashlib import sha256

import pytest

from intel_analysis_service.ml.model_registry import ModelRegistry


class Malicious:
    def __reduce__(self):
        import os
        return (os.system, ("echo hacked",))


def test_malicious_pickle_rejected(tmp_path):
    registry = ModelRegistry(tmp_path)
    model_dir = registry._model_dir("bad", "v1")
    model_dir.mkdir(parents=True)

    payload = pickle.dumps(Malicious())
    checksum = sha256(payload).hexdigest()
    with open(model_dir / "model.pkl", "wb") as fh:
        fh.write(payload)
    metadata = {
        "version": "v1",
        "timestamp": datetime.utcnow().isoformat(),
        "parameters": {},
        "checksum": checksum,
    }
    with open(model_dir / "metadata.json", "w") as fh:
        json.dump(metadata, fh)

    with pytest.raises(pickle.UnpicklingError):
        registry.load_model("bad", "v1")
