# A/B Testing Models

`ModelABTester` allows routing a portion of prediction traffic to different model versions.
Candidate models are loaded from the `ModelRegistry` and selected according to
user defined weights.

## Configuring Weights

Use the CLI tool to update the traffic split for a model:

```bash
python tools/cli_ab_testing.py my-model "1.0.0=80,1.1.0=20" --db sqlite:///registry.db --bucket ml-bucket
```

Weights are stored in `ab_weights.json` by default. The tester reloads the
models when weights change.

## Making Predictions

Create a tester instance and call `predict` with your input data:

```python
from yosai_intel_dashboard.src.models.ml import ModelRegistry
from yosai_intel_dashboard.src.services.ab_testing import ModelABTester

registry = ModelRegistry("sqlite:///registry.db", "ml-bucket")
tester = ModelABTester("my-model", registry)
result = tester.predict(data)
```

Each call randomly chooses a model version based on the configured weights and
logs which version produced the prediction.
