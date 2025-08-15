import pandas as pd
from sklearn.linear_model import LogisticRegression

from yosai_intel_dashboard.src.services.explainability_service import ExplainabilityService


def test_feature_importance_with_coefficients():
    X = pd.DataFrame({"a": [0, 1, 0, 1], "b": [1, 0, 1, 0]})
    y = [0, 1, 0, 1]
    model = LogisticRegression().fit(X, y)
    svc = ExplainabilityService()
    svc.register_model("demo", model, background_data=X)
    imp = svc.feature_importance("demo", X)
    assert set(imp.keys()) == {"a", "b"}
