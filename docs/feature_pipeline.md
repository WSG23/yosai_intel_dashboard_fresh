> **Note**: Import paths updated for clean architecture. Legacy imports are deprecated.

# Feature Pipeline

`FeaturePipeline` orchestrates feature extraction and transformation using the
existing `FeastFeatureStore` and `ModelRegistry` utilities.

## Transformation Flow

Raw event records are first normalised through the shared
`preprocess_events` contract. This function applies the project-wide
feature engineering steps and returns a dataframe enriched with
temporal, access, user and security attributes. The resulting features
are then passed into `FeaturePipeline` for any additional per-model
transformations before training or inference.

## Loading Definitions

```python
from yosai_intel_dashboard.src.models.ml.feature_pipeline import FeaturePipeline
pipe = FeaturePipeline("defs.yaml")
pipe.load_definitions()
```

Definitions are provided as JSON or YAML with a `features` list.

## Batch vs Real-time

```python
store = FeastFeatureStore(repo_path="feature_store")
pipe = FeaturePipeline("defs.yaml", feature_store=store)
entity_df = pd.DataFrame({"person_id": ["u1"], "event_timestamp": ["2024-01-01"]})
training = pipe.compute_batch_features(anomaly_service, entity_df)
serving = pipe.compute_online_features(anomaly_service, [{"person_id": "u1"}])
```

## Rollback

After registering a new model version you can revert:

```python
registry = ModelRegistry("sqlite:///registry.db", bucket="models")
pipe = FeaturePipeline("defs.yaml", registry=registry)
version = pipe.register_version("model", "model.joblib", {"acc": 0.9}, "hash")
pipe.rollback("model", version)
```

Rollback simply marks an earlier version as active via the registry.

## End-to-End Usage

```python
import pandas as pd
from sklearn.linear_model import LogisticRegression

from yosai_intel_dashboard.models.ml.pipeline_contract import preprocess_events
from yosai_intel_dashboard.models.ml.feature_pipeline import FeaturePipeline
from yosai_intel_dashboard.src.models.ml.training.pipeline import TrainingPipeline
from yosai_intel_dashboard.models.ml import ModelRegistry

# 1. Load and preprocess raw events
events = pd.read_csv("events.csv")
events = preprocess_events(events)

# 2. Transform features
pipe = FeaturePipeline("defs.yaml")
pipe.load_definitions()
X = pipe.fit_transform(events)
y = events["label"]

# 3. Train using the same contract
registry = ModelRegistry("sqlite:///registry.db", bucket="models")
tp = TrainingPipeline(registry)
tp.run(events, target_column="label", models={
    "logreg": (LogisticRegression(), {"C": [1.0]}),
})
```

The example demonstrates how preprocessing, feature transformation and model
training share the `preprocess_events` contract for consistent behaviour.
