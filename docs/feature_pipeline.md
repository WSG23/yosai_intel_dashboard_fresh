> **Note**: Import paths updated for clean architecture. Legacy imports are deprecated.

# Feature Pipeline

`FeaturePipeline` orchestrates feature extraction and transformation using the
existing `FeastFeatureStore` and `ModelRegistry` utilities.

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
