import pytest
import sys
import types

dash_mod = types.ModuleType("dash")
dash_dash_mod = types.ModuleType("dash.dash")
dash_dash_mod.no_update = object()
sys.modules.setdefault("dash", dash_mod)
sys.modules.setdefault("dash.dash", dash_dash_mod)
sys.modules.setdefault("bleach", types.ModuleType("bleach"))
sqlparse_mod = types.ModuleType("sqlparse")
sqlparse_mod.tokens = object()
sys.modules.setdefault("sqlparse", sqlparse_mod)

import pathlib
services_pkg = types.ModuleType("services")
services_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "services")]
sys.modules.setdefault("services", services_pkg)

from core.protocols import AnalyticsServiceProtocol

# Provide lightweight stubs for heavy service modules
analytics_service_stub = types.ModuleType("services.analytics_service")

class StubAnalyticsService(AnalyticsServiceProtocol):
    def get_dashboard_summary(self):
        return {}

    def analyze_access_patterns(self, days: int):
        return {}

    def detect_anomalies(self, data):
        return []

    def generate_report(self, report_type: str, params: dict):
        return {}

analytics_service_stub.AnalyticsService = StubAnalyticsService
sys.modules.setdefault("services.analytics_service", analytics_service_stub)

upload_reg_stub = types.ModuleType("services.upload.service_registration")
def _register_upload_services(container):
    container.register_singleton("upload_processor", object)
upload_reg_stub.register_upload_services = _register_upload_services
sys.modules.setdefault("services.upload.service_registration", upload_reg_stub)

# Provide lightweight stubs for heavy service modules
analytics_service_stub = types.ModuleType("services.analytics_service")

class StubAnalyticsService(AnalyticsServiceProtocol):
    def get_dashboard_summary(self):
        return {}

    def analyze_access_patterns(self, days: int):
        return {}

    def detect_anomalies(self, data):
        return []

    def generate_report(self, report_type: str, params: dict):
        return {}

analytics_service_stub.AnalyticsService = StubAnalyticsService
sys.modules.setdefault("services.analytics_service", analytics_service_stub)

from core.service_container import ServiceContainer
from core.protocols import (
    ConfigurationProtocol,
    AnalyticsServiceProtocol,
    SecurityServiceProtocol,
)
from config.complete_service_registration import register_all_services


class TestProtocolCompliance:
    def test_configuration_service_compliance(self):
        from config.config import ConfigManager
        for method in ["get_database_config", "get_app_config", "get_security_config", "reload_config"]:
            assert hasattr(ConfigManager, method)

    def test_analytics_service_compliance(self):
        from services.analytics_service import AnalyticsService
        for method in ["get_dashboard_summary", "analyze_access_patterns", "detect_anomalies", "generate_report"]:
            assert hasattr(AnalyticsService, method)

    def test_security_service_compliance(self):
        from core.security_validator import SecurityValidator
        for method in ["validate_input", "validate_file_upload", "sanitize_output", "check_permissions"]:
            assert hasattr(SecurityValidator, method)

    def test_all_registered_services_implement_protocols(self):
        container = ServiceContainer()
        import os
        for var in [
            "SECRET_KEY",
            "DB_PASSWORD",
            "AUTH0_CLIENT_ID",
            "AUTH0_CLIENT_SECRET",
            "AUTH0_DOMAIN",
            "AUTH0_AUDIENCE",
        ]:
            os.environ.setdefault(var, "test")
        register_all_services(container)
        results = container.validate_registrations()
        assert len(results["protocol_violations"]) == 0
        assert len(results["missing_dependencies"]) == 0
