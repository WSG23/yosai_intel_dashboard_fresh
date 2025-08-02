from __future__ import annotations

import sys
import types
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class ModelVersionMetric(Base):
    __tablename__ = "model_version_metrics"

    time = Column(DateTime(timezone=True), primary_key=True, default=datetime.utcnow)
    model_name = Column(String(100), primary_key=True)
    version = Column(String(50), primary_key=True)
    metric = Column(String(50), primary_key=True)
    value = Column(Float)


sys.modules[
    "yosai_intel_dashboard.src.services.timescale.models"
] = types.SimpleNamespace(Base=Base, ModelVersionMetric=ModelVersionMetric)

from monitoring.model_performance_tracker import ModelPerformanceTracker


def _make_tracker(rollback=None, canary=None):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return ModelPerformanceTracker(session, rollback_hook=rollback, canary_hook=canary)


def test_rollback_triggered_on_metric_drop():
    rollbacks = []
    tracker = _make_tracker(rollback=lambda name, ver: rollbacks.append((name, ver)))
    tracker.record_metrics("demo", "1.0.0", {"accuracy": 0.9})
    tracker.record_metrics("demo", "1.1.0", {"accuracy": 0.8})
    assert tracker.evaluate("demo", "1.1.0", threshold=0.05)
    assert rollbacks == [("demo", "1.0.0")]


def test_canary_invoked_for_improved_model():
    canaries = []
    tracker = _make_tracker(canary=lambda name, ver: canaries.append((name, ver)))
    tracker.record_metrics("demo", "1.0.0", {"accuracy": 0.8})
    tracker.record_metrics("demo", "1.1.0", {"accuracy": 0.85})
    assert not tracker.evaluate("demo", "1.1.0", threshold=0.05)
    assert canaries == [("demo", "1.1.0")]
