#!/usr/bin/env python3
"""
Complete Integration Tests for Analytics System
"""
import pandas as pd
import pytest
from yosai_intel_dashboard.models.base import ModelFactory

from yosai_intel_dashboard.src.services import create_analytics_service, get_analytics_service


def test_analytics_service_creation():
    """Test analytics service can be created"""
    service = get_analytics_service(create_analytics_service())
    assert service is not None
    assert hasattr(service, "health_check")


def test_analytics_with_sample_data():
    """Test analytics generation with sample data"""
    service = get_analytics_service(create_analytics_service())
    result = service.get_analytics_by_source("sample")

    assert result["status"] == "success"
    assert "total_rows" in result
    assert result["total_rows"] > 0


def test_model_factory():
    """Test model factory creates models correctly"""
    df = pd.DataFrame(
        {
            "user_id": ["user1", "user2"],
            "door_id": ["door1", "door2"],
            "access_result": ["Granted", "Denied"],
        }
    )

    models = ModelFactory.create_models_from_dataframe(df)
    assert "access" in models
    assert "anomaly" in models


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
    service = get_analytics_service(create_analytics_service())
    health = service.health_check()

    assert "service" in health
    assert health["service"] == "healthy"
    assert "timestamp" in health


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
