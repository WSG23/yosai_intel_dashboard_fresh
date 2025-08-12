#!/usr/bin/env python3
from __future__ import annotations

"""
Complete Integration Tests for Analytics System
"""
import pytest

from yosai_intel_dashboard.src.adapters.access_event_dataframe import dataframe_to_events
from yosai_intel_dashboard.src.core.domain.entities.base import AccessEventModel, ModelFactory


def test_analytics_service_creation():
    """Test analytics service can be created"""
    from yosai_intel_dashboard.src.services import (
        create_analytics_service,
        get_analytics_service,
    )

    service = get_analytics_service(create_analytics_service())
    assert service is not None
    assert hasattr(service, "health_check")


def test_analytics_with_sample_data():
    """Test analytics generation with sample data"""
    from yosai_intel_dashboard.src.services import (
        create_analytics_service,
        get_analytics_service,
    )

    service = get_analytics_service(create_analytics_service())
    result = service.get_analytics_by_source("sample")

    assert result["status"] == "success"
    assert "total_rows" in result
    assert result["total_rows"] > 0


def test_model_factory():
    """Test model factory creates models correctly"""
    class FakeDataFrame:
        def __init__(self, records):
            self._records = records
            self.empty = not records

        def to_dict(self, orient: str):
            assert orient == "records"
            return self._records

    df = FakeDataFrame(
        [
            {"user_id": "user1", "door_id": "door1", "access_result": "Granted"},
            {"user_id": "user2", "door_id": "door2", "access_result": "Denied"},
        ]
    )

    events = dataframe_to_events(df)
    direct_model = AccessEventModel()
    assert direct_model.load(events)
    assert isinstance(direct_model.events, list)
    assert direct_model.get_user_activity() == {"user1": 1, "user2": 1}
    assert direct_model.get_door_activity() == {"door1": 1, "door2": 1}

    models = ModelFactory.create_models_from_dataframe(df)
    assert "access" in models
    assert "anomaly" in models
    access_model = models["access"]
    assert isinstance(access_model.events, list)
    assert access_model.get_user_activity() == {"user1": 1, "user2": 1}
    assert access_model.get_door_activity() == {"door1": 1, "door2": 1}


def test_model_factory_absent(monkeypatch):
    """ModelFactory gracefully handles missing registry entry"""
    from importlib import reload

    import yosai_intel_dashboard.src.services.registry as reg

    original = reg.get_service

    def fake_get_service(name: str):
        if name in {
            "ModelFactory",
            "BaseModel",
            "AccessEventModel",
            "AnomalyDetectionModel",
        }:
            return None
        return original(name)

    monkeypatch.setattr(reg, "get_service", fake_get_service)
    import yosai_intel_dashboard.models as models_pkg

    reload(models_pkg)
    assert models_pkg.ModelFactory is None
    assert not models_pkg.BASE_MODELS_AVAILABLE


def test_health_check():
    """Test service health check"""
    from yosai_intel_dashboard.src.services import (
        create_analytics_service,
        get_analytics_service,
    )

    service = get_analytics_service(create_analytics_service())
    health = service.health_check()

    assert "service" in health
    assert health["service"] == "healthy"
    assert "timestamp" in health


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
