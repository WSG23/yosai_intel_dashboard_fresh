from __future__ import annotations

import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

pytest.importorskip("shap")
pytest.importorskip("lime")

from services.explainability_service import ExplainabilityService


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
