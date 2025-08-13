from datetime import timedelta

from yosai_intel_dashboard.optional_dependencies import import_optional

feast = import_optional("feast")
if feast:
    from feast import Entity, FeatureService, FeatureView, Field
    from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
        PostgreSQLSource,
    )
    from feast.types import Float32, Int64
else:  # pragma: no cover - fallback when Feast is unavailable
    Entity = FeatureService = FeatureView = Field = object
    PostgreSQLSource = object
    Float32 = Int64 = object

# Entities
person = Entity(name="person_id", join_keys=["person_id"])
door = Entity(name="door_id", join_keys=["door_id"])
facility = Entity(name="facility_id", join_keys=["facility_id"])

# Offline data source from PostgreSQL
access_events_source = PostgreSQLSource(
    name="access_events_source",
    table="access_events",
    timestamp_field="timestamp",
)

# Feature view with initial anomaly detection features
anomaly_features_view = FeatureView(
    name="anomaly_features",
    entities=[person, door, facility],
    ttl=timedelta(days=1),
    schema=[
        Field(name="door_entry_count_1h", dtype=Int64),
        Field(name="door_entry_mean_duration_1d", dtype=Float32),
        Field(name="user_entry_count_1d", dtype=Int64),
        Field(name="user_failed_entry_count_1d", dtype=Int64),
        Field(name="device_alerts_count_1d", dtype=Int64),
        Field(name="event_entry_ratio_1d", dtype=Float32),
        Field(name="device_downtime_ratio_1d", dtype=Float32),
        Field(name="user_high_risk_event_count_1d", dtype=Int64),
        Field(name="facility_occupancy_rate", dtype=Float32),
        Field(name="day_of_week", dtype=Int64),
    ],
    online=True,
    offline=True,
    source=access_events_source,
)

# Feature service for easy retrieval
anomaly_service = FeatureService(
    name="anomaly_detection_service",
    features=[anomaly_features_view],
)

__all__ = [
    "person",
    "door",
    "facility",
    "anomaly_features_view",
    "anomaly_service",
]
