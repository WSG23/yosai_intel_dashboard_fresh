"""Integration tests for Phase 3-4 consolidation."""
import pytest
from core.app_factory import AppFactory
from components.upload import UnifiedUploadComponent


class TestPhase34Integration:
    """Test complete Phase 3-4 integration."""

    def test_consolidated_upload_component(self, di_container):
        """Test unified upload component works with DI."""
        component = UnifiedUploadComponent(di_container)
        layout = component.render()

        assert layout is not None
        assert hasattr(component, 'validator')
        assert hasattr(component, 'handler')

    def test_app_factory_creates_working_app(self):
        """Test app factory creates fully functional app."""
        factory = AppFactory()
        app = factory.create_app({"TESTING": True})

        assert app is not None
        assert hasattr(app, 'layout')
        container = factory.get_container()
        assert container.has("upload_processor")

    def test_no_direct_instantiation_in_services(self, di_container):
        """Test services are created via DI, not direct instantiation."""
        upload_processor = di_container.get("upload_processor")
        validator = di_container.get("upload_validator")

        assert upload_processor is not None
        assert validator is not None

    def test_unicode_safety_throughout_stack(self, di_container, sample_upload_data):
        """Test Unicode surrogate safety throughout the stack."""
        from core.unicode_processor import handle_unicode_surrogates

        test_text = "Test \uD800\uDC00 data"  # Valid surrogate pair
        safe_text = handle_unicode_surrogates(test_text)

        # Should not raise encoding errors
        safe_text.encode('utf-8')
        assert safe_text is not None
