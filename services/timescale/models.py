from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AccessEvent(Base):
    """Timescale access event schema."""

    __tablename__ = "access_events"

    time = Column(DateTime(timezone=True), primary_key=True)
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


__all__ = ["Base", "AccessEvent", "AccessEvent5Min"]
