import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from yosai_intel_dashboard.src.services.explainability_service import ExplainabilityService

shap = pytest.importorskip("shap")
if not hasattr(shap.plots, "save"):
    pytest.skip("shap.plots.save not available", allow_module_level=True)


def test_visualize_model_creates_file(tmp_path):
    X = pd.DataFrame({"a": [0, 1, 0, 1], "b": [1, 0, 1, 0]})
    y = [0, 1, 0, 1]
    model = LogisticRegression().fit(X, y)
    svc = ExplainabilityService()
    svc.register_model("demo", model, background_data=X)
    out = tmp_path / "plot.png"
    svc.visualize_model("demo", X, out)
    assert out.exists()
