# Feature Store

The dashboard uses **Feast** to manage machine learning features.
Features are materialised to PostgreSQL for offline use and to Redis for
serving online requests. The feature repository lives under
`feature_store/` and includes the initial set of anomaly detection features.

## Configuration

`feature_store/feature_store.yaml` defines the online and offline stores.
Update the connection information to match your environment before running
`feast apply`.

## Available Features

The `anomaly_features` view exposes the following features:

1. `door_entry_count_1h`
2. `door_entry_mean_duration_1d`
3. `user_entry_count_1d`
4. `user_failed_entry_count_1d`
5. `device_alerts_count_1d`
6. `event_entry_ratio_1d`
7. `device_downtime_ratio_1d`
8. `user_high_risk_event_count_1d`
9. `facility_occupancy_rate`
10. `day_of_week`

Use the :class:`models.ml.feature_store.FeastFeatureStore` helper to fetch
historical or online features and to monitor basic feature drift.

## Feature Pipeline

See [feature_pipeline.md](feature_pipeline.md) for using the `FeaturePipeline`
class to perform batch and real-time feature computation and rollback of model
versions.
