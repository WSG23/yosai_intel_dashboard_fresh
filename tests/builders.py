from __future__ import annotations

import os
import pathlib
import sys
import types
from typing import Any, Dict

import pandas as pd

from config.complete_service_registration import register_all_services
from core.protocols import AnalyticsServiceProtocol
from core.service_container import ServiceContainer


class TestContainerBuilder:
    """Helper for constructing ServiceContainer instances for tests."""

    def __init__(self) -> None:
        self._container = ServiceContainer()
        self._stub_modules()

    # ------------------------------------------------------------------
    def _stub_modules(self) -> None:
        """Insert minimal stubs for heavy optional dependencies."""
        dash_mod = types.ModuleType("dash")
        dash_dash_mod = types.ModuleType("dash.dash")
        dash_dash_mod.no_update = object()
        sys.modules.setdefault("dash", dash_mod)
        sys.modules.setdefault("dash.dash", dash_dash_mod)
        sys.modules.setdefault("bleach", types.ModuleType("bleach"))
        sqlparse_mod = types.ModuleType("sqlparse")
        sqlparse_mod.tokens = object()
        sys.modules.setdefault("sqlparse", sqlparse_mod)

        services_pkg = types.ModuleType("services")
        services_pkg.__path__ = [
            str(pathlib.Path(__file__).resolve().parents[1] / "services")
        ]
        sys.modules.setdefault("services", services_pkg)

        analytics_stub = types.ModuleType("services.analytics_service")

        class StubAnalyticsService(AnalyticsServiceProtocol):
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

        analytics_stub.AnalyticsService = StubAnalyticsService
        sys.modules.setdefault("services.analytics_service", analytics_stub)

        upload_reg_stub = types.ModuleType("services.upload.service_registration")

        def _register_upload_services(container: ServiceContainer) -> None:
            container.register_singleton("upload_processor", object)

        upload_reg_stub.register_upload_services = _register_upload_services
        sys.modules.setdefault("services.upload.service_registration", upload_reg_stub)

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
