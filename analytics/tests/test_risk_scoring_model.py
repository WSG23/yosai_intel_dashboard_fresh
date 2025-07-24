import sys
from pathlib import Path
import pandas as pd

# Ensure project root is on sys.path when running tests directly
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import importlib.util

MODULE_DIR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "analytics.risk_scoring_model", MODULE_DIR / "risk_scoring_model.py"
)
risk_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(risk_module)
train_risk_model = risk_module.train_risk_model
predict_risk_score = risk_module.predict_risk_score


class DummyRegistry:
    def __init__(self) -> None:
        self.registered = False
        self.active_version = None

    def register_model(self, name, model_path, metrics, dataset_hash, **kwargs):
        self.registered = True
        class Rec:
            def __init__(self) -> None:
                self.version = "0.1.0"
        return Rec()

    def set_active_version(self, name, version):
        self.active_version = version


def test_train_and_predict():
    df = pd.DataFrame(
        {
            "f1": [0, 1, 0, 1],
            "f2": [1, 1, 0, 0],
            "label": [0, 1, 0, 1],
        }
    )
    registry = DummyRegistry()
    model, scaler = train_risk_model(df, model_registry=registry)

    assert registry.registered
    assert registry.active_version == "0.1.0"

    preds = predict_risk_score(model, df[["f1", "f2"]], scaler)
    assert len(preds) == len(df)
    assert ((preds >= 0) & (preds <= 1)).all()
