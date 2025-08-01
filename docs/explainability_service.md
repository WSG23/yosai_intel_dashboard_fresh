# Explainability Service

`ExplainabilityService` exposes common ML explainability techniques for any
scikit-learn compatible model.  Models are registered with background data and
the service generates explanations on demand.

## Features

- SHAP value calculation for global and per-row insights
- LIME explanations for individual predictions
- Feature importance ranking using model attributes or SHAP
- Naive counterfactual example generation
- SHAP based visualization helper
- Bias detection metrics with `fairlearn`
- Natural language explanation synthesis

## Example

```python
from yosai_intel_dashboard.src.services.explainability_service import ExplainabilityService
from sklearn.linear_model import LogisticRegression
import pandas as pd

X = pd.DataFrame({"a": [0, 1], "b": [1, 0]})
y = [0, 1]
model = LogisticRegression().fit(X, y)

svc = ExplainabilityService()
svc.register_model("demo", model, background_data=X)
values = svc.shap_values("demo", X)
```
