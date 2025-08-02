"""TimescaleDB table definitions and helpers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, MetaData, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.engine import Connection
from sqlalchemy.orm import declarative_base

# ---------------------------------------------------------------------------
# Metadata with hypertable policy information
# ---------------------------------------------------------------------------

metadata = MetaData()

# Policies applied after creating the tables. Chunks are compressed after
# thirty days (hot storage) and retained for one year before being dropped.
metadata.info["hot_interval"] = "30 days"
metadata.info["retention_interval"] = "365 days"

Base = declarative_base(metadata=metadata)


class AccessEvent(Base):
    """Timescale access event schema."""

    __tablename__ = "access_events"

    time = Column(DateTime(timezone=True), primary_key=True, default=datetime.utcnow)
    event_id = Column(UUID(as_uuid=True), primary_key=True)
    person_id = Column(String(50), index=True)
    door_id = Column(String(50), index=True)
    facility_id = Column(String(50), index=True)
    access_result = Column(String(20))
    badge_status = Column(String(20))
    response_time_ms = Column(Integer)
    metadata = Column(JSONB)


class AccessEvent5Min(Base):
    """Continuous aggregate summarising five minute buckets."""

    __tablename__ = "access_events_5min"

    bucket = Column(DateTime(timezone=True), primary_key=True)
    facility_id = Column(String(50), primary_key=True)
    event_count = Column(Integer)


class AccessEventHourly(Base):
    """Continuous aggregate summarising hourly buckets."""

    __tablename__ = "access_events_hourly"

    bucket = Column(DateTime(timezone=True), primary_key=True)
    facility_id = Column(String(50), primary_key=True)
    event_count = Column(Integer)


class ModelMonitoringEvent(Base):
    """Recorded model evaluation metrics."""

    __tablename__ = "model_monitoring_events"

    time = Column(DateTime(timezone=True), primary_key=True)
    model_name = Column(String(100), index=True)
    version = Column(String(50))
    metric = Column(String(50))
    value = Column(Float)
    drift_type = Column(String(50))
    status = Column(String(20))


class ModelVersionMetric(Base):
    """Aggregated metrics for each model version."""

    __tablename__ = "model_version_metrics"

    time = Column(DateTime(timezone=True), primary_key=True, default=datetime.utcnow)
    model_name = Column(String(100), primary_key=True)
    version = Column(String(50), primary_key=True)
    metric = Column(String(50), primary_key=True)
    value = Column(Float)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def ensure_hypertable(conn: Connection, table: str, time_column: str = "time") -> None:
    """Create hypertable for ``table`` if it doesn't already exist."""

    conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
    conn.execute(
        text(
            "SELECT create_hypertable(:table, :time, if_not_exists => TRUE)"
        ).bindparams(table=table, time=time_column)
    )


def apply_policies(conn: Connection, table: str = "access_events") -> None:
    """Apply compression and retention policies for ``table``."""

    hot = Base.metadata.info.get("hot_interval", "30 days")
    retention = Base.metadata.info.get("retention_interval", "365 days")
    conn.execute(
        text(
            f"ALTER TABLE {table} SET ("  # nosec B608
            "timescaledb.compress, "
            "timescaledb.compress_orderby = 'time DESC', "
            "timescaledb.compress_segmentby = 'facility_id')"
        )
    )
    conn.execute(
        text(
            "SELECT add_compression_policy(:table, INTERVAL :hot, if_not_exists => TRUE)"
        ).bindparams(table=table, hot=hot)
    )
    conn.execute(
        text(
            "SELECT add_retention_policy(:table, INTERVAL :retention, if_not_exists => TRUE)"
        ).bindparams(table=table, retention=retention)
    )


__all__ = [
    "Base",
    "AccessEvent",
    "AccessEvent5Min",
    "AccessEventHourly",
    "ModelMonitoringEvent",
    "ModelVersionMetric",
]
