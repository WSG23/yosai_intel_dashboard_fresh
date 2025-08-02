> **Note**: Import paths updated for clean architecture. Legacy imports are deprecated.

# Training Pipeline

`TrainingPipeline` automates cross validation, hyper-parameter tuning and model registration.
This guide shows how to run `models/ml/training/pipeline.py` and configure the
underlying `ModelRegistry`.

## Requirements

Install the dependencies listed in `requirements.txt` plus any ML libraries
(such as scikit-learn, xgboost or tensorflow) used by your models. The
pipeline also logs metrics to MLflow.

Start a local MLflow server if you do not already have one:

```bash
mlflow ui --backend-store-uri ./mlruns
```

## Example Usage

Create a small driver script or use the Python prompt to execute the pipeline:

```python
from yosai_intel_dashboard.src.models.ml.model_registry import ModelRegistry
from yosai_intel_dashboard.src.models.ml.training.pipeline import TrainingPipeline
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

# Training data with a column named 'label'
df = pd.read_csv("train.csv")

registry = ModelRegistry(
    "sqlite:///registry.db",  # database URL
    bucket="ml-models",       # S3 bucket for artifacts
    mlflow_uri="http://localhost:5000",  # MLflow tracking URI
)

pipeline = TrainingPipeline(registry, mlflow_uri="http://localhost:5000")
models = {"rf": (RandomForestClassifier(), {"n_estimators": [50, 100]})}
result = pipeline.run(df, target_column="label", models=models)
print("Best metrics:", result.metrics)
```

After the run finishes you can open the MLflow UI to inspect the metrics and
artifacts. The registered model artifact is uploaded to the configured S3
bucket and recorded in the registry database.

## Configuring `ModelRegistry`

`ModelRegistry(database_url, bucket, mlflow_uri=None)` stores metadata in the
specified database and uploads artifacts to the given S3 bucket. The tracking
URI is optional; when provided MLflow logs are sent to that server instead of
the local `mlruns` directory.

Versions are bumped automatically when registering a model. If metrics improve
by at least the thresholds supplied to `ModelRegistry(metric_thresholds=...)`
the minor version is incremented and the patch number is reset. Otherwise only
the patch version is increased. New models start at `0.1.0`.

## Registering Artifacts Manually

You can also register artifacts directly using MLflow's CLI:

```bash
mlflow artifacts log-artifact model.joblib --run-id <run-id>
```

Models registered through `TrainingPipeline` already call `mlflow.log_artifact`
and `ModelRegistry.register_model` under the hood, so manual registration is
rarely needed.
