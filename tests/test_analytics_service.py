import pandas as pd

from services.analytics_service import AnalyticsService
from tests.fake_configuration import FakeConfiguration


def _make_df():
    return pd.DataFrame(
        {
            "person_id": ["u1", "u2", "u1"],
            "door_id": ["d1", "d2", "d1"],
            "access_result": ["Granted", "Denied", "Granted"],
            "timestamp": [
                "2024-01-01 10:00:00",
                "2024-01-02 11:00:00",
                "2024-01-02 12:00:00",
            ],
        }
    )


def test_process_uploaded_data_directly_success():
    service = AnalyticsService()
    df = _make_df()
    result = service._process_uploaded_data_directly({"file.csv": df})
    assert result["status"] == "success"
    assert result["total_events"] == 3
    assert result["active_users"] == 2
    assert result["active_doors"] == 2
    assert result["processing_info"]["file.csv"]["rows"] == 3


def test_process_uploaded_data_directly_error():
    service = AnalyticsService()
    result = service._process_uploaded_data_directly({})
    assert result["status"] == "error"


def test_regular_analysis_all_sections():
    service = AnalyticsService()
    df = _make_df()
    res = service._regular_analysis(df, ["basic", "temporal", "user", "access"])
    assert res["total_events"] == 3
    assert res["analysis_type"] == "regular"
    assert res["basic_stats"]["unique_person_id"] == 2
    assert res["user_analysis"]["active_users"] == 2
    assert res["access_analysis"]["access_results"] == {"Granted": 2, "Denied": 1}
    assert res["temporal_analysis"]["total_events"] == 3


def test_get_real_uploaded_data(monkeypatch):
    df1 = _make_df().iloc[:2]
    df2 = _make_df().iloc[1:]
    service = AnalyticsService()
    monkeypatch.setattr(
        service, "load_uploaded_data", lambda: {"a.csv": df1, "b.csv": df2}
    )
    summary = service._get_real_uploaded_data()
    assert summary["status"] == "success"
    assert summary["files_processed"] == 2
    assert summary["original_total_rows"] == len(df1) + len(df2)
    assert summary["total_events"] == len(df1) + len(df2)
    assert summary["active_users"] == 2
    assert summary["active_doors"] >= 1


def test_get_real_uploaded_data_no_files(monkeypatch):
    service = AnalyticsService()
    monkeypatch.setattr(service, "load_uploaded_data", lambda: {})
    res = service._get_real_uploaded_data()
    assert res["status"] == "no_data"


def test_service_receives_config(monkeypatch):
    """Provided config should be stored on the service instance."""

    import services.analytics_service as mod

    # ensure a fresh global instance
    mod._analytics_service = None

    # allow instantiation without implementing abstract methods
    monkeypatch.setattr(mod.AnalyticsService, "__abstractmethods__", frozenset())

    captured = {}

    def fake_init(
        self,
        database=None,
        data_processor=None,
        *,
        config=None,
        event_bus=None,
        storage=None,
    ):
        captured["database"] = database
        captured["config"] = config
        self.database = database
        self.config = config

    monkeypatch.setattr(mod.AnalyticsService, "__init__", fake_init)

    cfg = FakeConfiguration()
    service = mod.get_analytics_service(config_provider=cfg)

    assert service.config is cfg
    assert service.database is None
    assert captured["config"] is cfg
    assert captured["database"] is None
