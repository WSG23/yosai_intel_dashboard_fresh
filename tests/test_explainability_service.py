import importlib
import pathlib
import sys
import types

import pandas as pd
from sklearn.linear_model import LogisticRegression

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[1] / "services"
services_mod = sys.modules.get("services")
if services_mod is None:
    services_mod = types.ModuleType("services")
    sys.modules["services"] = services_mod
services_mod.__path__ = [str(SERVICES_PATH)]

from yosai_intel_dashboard.src.services.explainability_service import ExplainabilityService


def _make_dataset():
    X = pd.DataFrame({"a": [0, 1, 0, 1], "b": [1, 0, 1, 0]})
    y = [0, 1, 0, 1]
    return X, y


def test_shap_values():
    X, y = _make_dataset()
    model = LogisticRegression().fit(X, y)
    svc = ExplainabilityService()
    svc.register_model("demo", model, background_data=X)
    values = svc.shap_values("demo", X)
    assert values.shape == X.shape  # nosec B101


def test_lime_explanation():
    X, y = _make_dataset()
    model = LogisticRegression().fit(X, y)
    svc = ExplainabilityService()
    svc.register_model("demo", model, background_data=X)
    explanation = svc.lime_explanation("demo", X, 0)
    assert isinstance(explanation, dict)  # nosec B101
    assert explanation  # nosec B101
