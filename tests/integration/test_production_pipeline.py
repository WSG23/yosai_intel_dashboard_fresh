import pandas as pd
import pytest

from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


def create_production_container() -> ServiceContainer:
    """Return a container with all production services registered."""
    from startup.service_registration import register_all_application_services

    container = ServiceContainer()
    register_all_application_services(container)
    return container


def test_complete_upload_analytics_pipeline(tmp_path):
    container = create_production_container()
    upload_service = container.get("upload_data_service")
    df = pd.DataFrame(
        {
            "person_id": ["u1", "u2"],
            "door_id": ["d1", "d2"],
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02"]),
        }
    )
    upload_service.store.add_file("events.csv", df)
    processor = container.get("upload_analytics_processor")
    processor.load_uploaded_data = upload_service.get_uploaded_data
    result = processor.analyze_uploaded_data()
    assert result["status"] == "success"
    assert result["total_events"] > 0
    assert result["active_users"] > 0
    assert result["active_doors"] > 0


def test_invalid_file():
    container = create_production_container()
    processor = container.get("upload_analytics_processor")
    def loader():
        raise FileNotFoundError("invalid file")
    processor.load_uploaded_data = loader
    result = processor.analyze_uploaded_data()
    assert result["status"] == "error"
    assert "invalid file" in result["message"].lower()


def test_large_file():
    container = create_production_container()
    processor = container.get("upload_analytics_processor")
    def loader():
        raise MemoryError("file too large")
    processor.load_uploaded_data = loader
    result = processor.analyze_uploaded_data()
    assert result["status"] == "error"
    assert "file too large" in result["message"].lower()


def test_malformed_data():
    container = create_production_container()
    processor = container.get("upload_analytics_processor")
    def loader():
        raise ValueError("malformed")
    processor.load_uploaded_data = loader
    result = processor.analyze_uploaded_data()
    assert result["status"] == "error"
    assert "malformed" in result["message"].lower()
