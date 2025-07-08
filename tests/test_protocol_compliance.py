from tests.builders import TestContainerBuilder


class TestProtocolCompliance:
    def test_configuration_service_compliance(self):
        from config.config import ConfigManager

        for method in [
            "get_database_config",
            "get_app_config",
            "get_security_config",
            "reload_config",
        ]:
            assert hasattr(ConfigManager, method)

    def test_analytics_service_compliance(self):
        from services.analytics_service import AnalyticsService

        for method in [
            "get_dashboard_summary",
            "analyze_access_patterns",
            "detect_anomalies",
            "generate_report",
        ]:
            assert hasattr(AnalyticsService, method)

    def test_security_service_compliance(self):
        from core.security_validator import SecurityValidator

        for method in [
            "validate_input",
            "validate_file_upload",
            "sanitize_output",
            "check_permissions",
        ]:
            assert hasattr(SecurityValidator, method)

    def test_all_registered_services_implement_protocols(self):
        container = TestContainerBuilder().with_all_services().build()
        results = container.validate_registrations()
        assert len(results["protocol_violations"]) == 0
        assert len(results["missing_dependencies"]) == 0
