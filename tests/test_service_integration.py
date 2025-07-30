import pytest

from tests.builders import TestContainerBuilder


class TestServiceIntegration:
    @pytest.fixture
    def configured_container(self):
        return TestContainerBuilder().with_all_services().build()

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

    def test_new_service_registrations(self, configured_container):
        loader = configured_container.get("data_loader")
        processor = configured_container.get("data_processing_service")
        reporter = configured_container.get("report_generator")
        publisher = configured_container.get("publisher")

        assert loader is not None
        assert processor is not None
        assert reporter is not None
        assert publisher is not None
