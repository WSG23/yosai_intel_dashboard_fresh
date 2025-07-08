from __future__ import annotations

import os
from typing import Any, Dict

import pandas as pd

from config.complete_service_registration import register_all_services
from core.protocols import AnalyticsServiceProtocol
from core.service_container import ServiceContainer


class TestContainerBuilder:
    """Helper for constructing ServiceContainer instances for tests."""


    def __init__(self) -> None:
        self._container = ServiceContainer()

    # ------------------------------------------------------------------
    def with_dash_stubs(self) -> "TestContainerBuilder":
        class _Dash:
            no_update = object()

        self._container.register_singleton("dash", _Dash)
        return self

    # ------------------------------------------------------------------
    def with_fake_analytics_service(self) -> "TestContainerBuilder":
        class FakeAnalyticsService(AnalyticsServiceProtocol):
            def get_dashboard_summary(self) -> Dict[str, Any]:
                return {}

            def analyze_access_patterns(self, days: int) -> Dict[str, Any]:
                return {}

            def detect_anomalies(self, data: Any) -> list[Any]:
                return []

            def generate_report(
                self, report_type: str, params: Dict[str, Any]
            ) -> Dict[str, Any]:
                return {}

        self._container.register_singleton(
            "analytics_service",
            FakeAnalyticsService,
            protocol=AnalyticsServiceProtocol,
        )
        return self

    # ------------------------------------------------------------------
    def with_upload_services(self) -> "TestContainerBuilder":
        self._container.register_singleton("upload_processor", object)
        return self

    # ------------------------------------------------------------------
    def with_env_defaults(self) -> "TestContainerBuilder":
        for var in [
            "SECRET_KEY",
            "DB_PASSWORD",
            "AUTH0_CLIENT_ID",
            "AUTH0_CLIENT_SECRET",
            "AUTH0_DOMAIN",
            "AUTH0_AUDIENCE",
        ]:
            os.environ.setdefault(var, "test")
        return self

    # ------------------------------------------------------------------
    def with_all_services(self) -> "TestContainerBuilder":
        register_all_services(self._container)
        return self

    # ------------------------------------------------------------------
    def build(self) -> ServiceContainer:
        return self._container


class TestDataBuilder:
    """Utility for constructing sample analytics dataframes."""

    def __init__(self) -> None:
        self._rows: list[Dict[str, Any]] = []

    def add_row(
        self,
        *,
        timestamp: str = "2024-01-01 00:00:00",
        person_id: str = "u1",
        token_id: str = "t1",
        door_id: str = "d1",
        access_result: str = "Granted",
    ) -> "TestDataBuilder":
        self._rows.append(
            {
                "timestamp": pd.to_datetime(timestamp),
                "person_id": person_id,
                "token_id": token_id,
                "door_id": door_id,
                "access_result": access_result,
            }
        )
        return self

    def build_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self._rows)

    def as_upload_dict(self, filename: str = "sample.csv") -> Dict[str, pd.DataFrame]:
        return {filename: self.build_dataframe()}
