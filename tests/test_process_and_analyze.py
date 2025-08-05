from __future__ import annotations

from tests.infrastructure import TestInfrastructure

factory = TestInfrastructure().setup_environment()

ua = factory.upload_processor()


def test_process_then_analyze(monkeypatch):
    data = {"sample.csv": factory.dataframe()}
    monkeypatch.setattr(ua, "load_uploaded_data", lambda: data)
    result = ua.analyze_uploaded_data()
    assert result["status"] == "success"
    assert result["rows"] == 1
