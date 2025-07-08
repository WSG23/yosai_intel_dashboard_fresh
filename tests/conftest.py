"""Test configuration with comprehensive DI fixtures."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
stub_dir = Path(__file__).resolve().parent / "stubs"
sys.path.insert(0, str(stub_dir))

import shutil
import tempfile
from typing import Generator

import pandas as pd
import pytest

from core.service_container import ServiceContainer
from core.app_factory import AppFactory
from config.complete_service_registration import register_all_application_services


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def di_container() -> ServiceContainer:
    """Create fully configured DI container for tests."""
    container = ServiceContainer()
    register_all_application_services(container)
    return container


@pytest.fixture
def app_factory() -> AppFactory:
    """Create app factory with DI for testing."""
    return AppFactory()


@pytest.fixture
def configured_app(app_factory: AppFactory):
    """Create fully configured app for integration tests."""
    return app_factory.create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })


@pytest.fixture
def upload_service(di_container: ServiceContainer):
    """Get upload service from DI container."""
    return di_container.get("upload_processor")


@pytest.fixture
def upload_validator(di_container: ServiceContainer):
    """Get upload validator from DI container."""
    return di_container.get("upload_validator")


@pytest.fixture
def file_processor(di_container: ServiceContainer):
    """Get file processor from DI container."""
    return di_container.get("file_processor")


@pytest.fixture
def mock_services(di_container: ServiceContainer, monkeypatch):
    """Setup mock services in DI container for testing."""
    from unittest.mock import Mock

    # Create mocks
    mock_upload_processor = Mock()
    mock_validator = Mock()
    mock_file_processor = Mock()

    # Configure mocks with Unicode safety
    mock_upload_processor.process_upload.return_value = {"status": "success"}
    mock_validator.validate_file.return_value = True
    mock_file_processor.process_file.return_value = pd.DataFrame()

    # Patch in DI container
    monkeypatch.setattr(di_container, "_instances", {
        "upload_processor": mock_upload_processor,
        "upload_validator": mock_validator,
        "file_processor": mock_file_processor,
    })

    return {
        "upload_processor": mock_upload_processor,
        "validator": mock_validator,
        "file_processor": mock_file_processor,
    }


@pytest.fixture
def sample_upload_data() -> pd.DataFrame:
    """Sample upload data with Unicode characters for testing."""
    return pd.DataFrame([
        {
            "name": "Test André",  # Unicode test
            "value": 123,
            "notes": "Sample données",  # Unicode test
        },
        {
            "name": "Test José",
            "value": 456,
            "notes": "More données",
        },
    ])


@pytest.fixture
def mock_auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setup required authentication environment variables."""
    auth_vars = {
        "AUTH0_CLIENT_ID": "test_client",
        "AUTH0_CLIENT_SECRET": "test_secret",
        "AUTH0_DOMAIN": "test.auth0.com",
        "AUTH0_AUDIENCE": "test_audience",
        "SECRET_KEY": "test_secret_key",
        "DB_PASSWORD": "test_db_password",
    }
    for key, value in auth_vars.items():
        monkeypatch.setenv(key, value)


# Helper functions for DI testing

def assert_service_registered(container: ServiceContainer, service_name: str) -> None:
    """Assert that a service is properly registered in DI container."""
    assert container.has(service_name), f"Service '{service_name}' not registered"
    service = container.get(service_name)
    assert service is not None, f"Service '{service_name}' is None"


def assert_protocol_compliance(service, protocol_class) -> None:
    """Assert that a service implements the required protocol."""
    assert isinstance(service, protocol_class), f"Service does not implement {protocol_class.__name__}"
