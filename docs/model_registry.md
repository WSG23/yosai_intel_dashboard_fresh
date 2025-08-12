# Model Registry Policy

The model registry tracks every trained model version and manages which
version is currently active. When a new model version is proposed for
activation, its metrics are compared against those of the active model.

## Drift thresholds

`ModelRegistry` accepts a `drift_thresholds` mapping that defines the
maximum allowed absolute difference for each metric. During activation
(`set_active_version`), the registry verifies that the difference between
the new version's metrics and the active version's metrics does not exceed
the configured thresholds. If any metric drifts beyond its threshold, the
activation is rejected.

## Rollback

Every time a new model is activated, the previous active version is stored
in an internal history. The `rollback_model(name)` API restores the most
recently active version for the given model, enabling quick reversions if
an activation causes issues.

