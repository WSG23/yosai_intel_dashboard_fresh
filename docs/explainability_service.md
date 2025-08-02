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

## Prediction Audit Trail

During inference the analytics microservice now computes SHAP values for each
prediction and records them alongside a generated ``prediction_id``.  Each
record stores the model name, version and timestamp creating an auditable trail
of explanations.

### API Usage

The ``prediction_id`` is returned from the prediction endpoint.  Use it to
retrieve the stored explanation via:

```
GET /api/v1/explanations/{prediction_id}
```

The route requires standard analytics read permissions and returns the SHAP
values and metadata for the requested prediction.
