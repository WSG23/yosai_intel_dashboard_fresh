import types

import dash_bootstrap_components as dbc
import pytest
from dash import html

pytestmark = pytest.mark.usefixtures("fake_dbc")

import pages.deep_analytics.callbacks as cb


def test_run_service_analysis_success(monkeypatch):
    def fake_analyze(ds, at):
        return {
            "analysis_type": at.title(),
            "data_source": ds,
            "total_events": 5,
            "unique_users": 2,
            "success_rate": 0.9,
        }

    monkeypatch.setattr(cb, "analyze_data_with_service", fake_analyze)

    result = cb.run_service_analysis("service:test", "security")
    assert isinstance(result, dbc.Card)


def test_run_service_analysis_error(monkeypatch):
    def fake_analyze(ds, at):
        return {"error": "boom"}

    monkeypatch.setattr(cb, "analyze_data_with_service", fake_analyze)

    result = cb.run_service_analysis("service:test", "security")
    assert isinstance(result, dbc.Alert)


def test_run_unique_patterns_analysis(monkeypatch):
    class FakeService:
        def get_unique_patterns_analysis(self, data_source):
            return {
                "status": "success",
                "data_summary": {
                    "total_records": 1,
                    "date_range": {"span_days": 1},
                    "unique_entities": {"users": 1, "devices": 1},
                },
                "user_patterns": {
                    "user_classifications": {
                        "power_users": [],
                        "regular_users": [],
                        "occasional_users": [],
                        "single_door_users": [],
                        "multi_door_users": [],
                        "problematic_users": [],
                    },
                    "user_statistics": {
                        "mean_events_per_user": 1,
                        "mean_doors_per_user": 1,
                    },
                },
                "device_patterns": {
                    "device_classifications": {
                        "high_traffic_devices": [],
                        "moderate_traffic_devices": [],
                        "low_traffic_devices": [],
                        "secure_devices": [],
                        "popular_devices": [],
                        "problematic_devices": [],
                    },
                    "device_statistics": {"mean_events_per_device": 1},
                },
                "interaction_patterns": {"total_unique_interactions": 1},
                "temporal_patterns": {
                    "peak_hours": [],
                    "peak_days": [],
                    "hourly_distribution": {},
                },
                "access_patterns": {
                    "overall_success_rate": 1,
                    "users_with_low_success": 0,
                    "devices_with_low_success": 0,
                },
                "recommendations": [],
                "analysis_timestamp": "now",
            }

    monkeypatch.setattr(cb, "AnalyticsService", lambda: FakeService())
    result = cb.run_unique_patterns_analysis("service:test")
    assert isinstance(result, html.Div)


def test_run_unique_patterns_analysis_no_data(monkeypatch):
    class FakeService:
        def get_unique_patterns_analysis(self, data_source):
            return {"status": "no_data"}

    monkeypatch.setattr(cb, "AnalyticsService", lambda: FakeService())
    result = cb.run_unique_patterns_analysis("service:test")
    assert isinstance(result, dbc.Alert)
