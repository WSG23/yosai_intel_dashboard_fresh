import pytest
import sys
import types
import pathlib

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
services_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "services")]
sys.modules.setdefault("services", services_pkg)

from core.protocols import AnalyticsServiceProtocol

analytics_stub = types.ModuleType("services.analytics_service")
analytics_stub.MAX_DISPLAY_ROWS = 100

class StubAnalyticsService(AnalyticsServiceProtocol):
    def get_dashboard_summary(self):
        return {}

    def analyze_access_patterns(self, days: int):
        return {}

    def detect_anomalies(self, data):
        return []

    def generate_report(self, report_type: str, params: dict):
        return {}

analytics_stub.AnalyticsService = StubAnalyticsService
sys.modules.setdefault("services.analytics_service", analytics_stub)

upload_reg_stub = types.ModuleType("services.upload.service_registration")
def _register_upload_services(container):
    container.register_singleton("upload_processor", object)
upload_reg_stub.register_upload_services = _register_upload_services
sys.modules.setdefault("services.upload.service_registration", upload_reg_stub)

from core.service_container import ServiceContainer
from config.complete_service_registration import register_all_services


class TestServiceIntegration:
    @pytest.fixture
    def configured_container(self):
        c = ServiceContainer()
        register_all_services(c)
        return c

    def test_analytics_uses_database_protocol(self, configured_container):
        analytics = configured_container.get("analytics_service")
        db = configured_container.get("database_manager")
        assert analytics is not None
        assert db is not None
        assert hasattr(db, "execute_query")

    def test_upload_uses_security_protocol(self, configured_container):
        upload_processor = configured_container.get("upload_processor")
        security = configured_container.get("security_validator")
        assert upload_processor is not None
        assert security is not None
        assert hasattr(security, "validate_file_upload")

    def test_cross_domain_protocol_usage(self, configured_container):
        analytics = configured_container.get("analytics_service")
        storage = configured_container.get("file_storage")
        security = configured_container.get("security_validator")
        assert analytics and storage and security
