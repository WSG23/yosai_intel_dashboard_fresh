"""Complete service registration for all domains."""
from core.service_container import ServiceContainer
from typing import Any
import pandas as pd
from core.protocols import (
    ConfigurationProtocol,
    DatabaseProtocol,
    LoggingProtocol,
    EventBusProtocol,
    AnalyticsServiceProtocol,
    SecurityServiceProtocol,
    ExportServiceProtocol,
)
from services.analytics.protocols import DataProcessorProtocol, ReportGeneratorProtocol
from services.security.protocols import AuthenticationProtocol, AuthorizationProtocol
from core.storage.protocols import FileStorageProtocol, DatabaseStorageProtocol


def register_all_services(container: ServiceContainer) -> None:
    """Register all services with protocol interfaces."""

    register_core_services(container)
    register_analytics_services(container)
    register_security_services(container)
    register_storage_services(container)
    register_export_services(container)

    from services.upload.service_registration import register_upload_services
    register_upload_services(container)


def register_core_services(container: ServiceContainer) -> None:
    from config.config import ConfigManager
    from config.database_manager import DatabaseManager, DatabaseConfig
    from core.logging import LoggingService
    from core.events import EventBus

    container.register_singleton(
        "config_manager",
        ConfigManager,
        protocol=ConfigurationProtocol,
    )

    class SimpleDatabase(DatabaseProtocol):
        def __init__(self):
            pass

        def execute_query(self, query: str, params: tuple | None = None):
            return pd.DataFrame()

        def execute_command(self, command: str, params: tuple | None = None) -> None:
            pass

        def health_check(self) -> bool:
            return True

        def begin_transaction(self) -> Any:
            return object()

    container.register_singleton(
        "database_manager",
        SimpleDatabase,
        protocol=DatabaseProtocol,
    )

    container.register_singleton(
        "logging_service",
        LoggingService,
        protocol=LoggingProtocol,
    )

    container.register_singleton(
        "event_bus",
        EventBus,
        protocol=EventBusProtocol,
    )


def register_analytics_services(container: ServiceContainer) -> None:
    from services.analytics_service import AnalyticsService
    from services.analytics.data_processor import DataProcessor
    from services.analytics.report_generator import ReportGenerator

    container.register_singleton(
        "analytics_service",
        AnalyticsService,
        protocol=AnalyticsServiceProtocol,
    )
    container.register_singleton(
        "data_processor",
        DataProcessor,
        protocol=DataProcessorProtocol,
    )
    container.register_transient(
        "report_generator",
        ReportGenerator,
        protocol=ReportGeneratorProtocol,
    )


def register_security_services(container: ServiceContainer) -> None:
    from core.security_validator import SecurityValidator
    # Placeholder auth/authorization services
    class AuthenticationService:
        def authenticate_user(self, username: str, password: str) -> dict:
            return {"user": username, "valid": True}

        def validate_token(self, token: str) -> dict:
            return {"token": token, "valid": True}

    class AuthorizationService:
        def check_permission(self, user_id: str, resource: str, action: str) -> bool:
            return True

        def get_user_roles(self, user_id: str) -> list[str]:
            return ["admin"]

    container.register_singleton(
        "security_validator",
        SecurityValidator,
        protocol=SecurityServiceProtocol,
    )
    container.register_singleton(
        "authentication_service",
        AuthenticationService,
        protocol=AuthenticationProtocol,
    )
    container.register_singleton(
        "authorization_service",
        AuthorizationService,
        protocol=AuthorizationProtocol,
    )


def register_storage_services(container: ServiceContainer) -> None:
    from core.storage.file_storage import FileStorageService
    from core.storage.database_storage import DatabaseStorageService

    container.register_singleton(
        "file_storage",
        FileStorageService,
        protocol=FileStorageProtocol,
    )
    container.register_singleton(
        "database_storage",
        DatabaseStorageService,
        protocol=DatabaseStorageProtocol,
    )


def register_export_services(container: ServiceContainer) -> None:
    from services.export_service import ExportService

    container.register_transient(
        "export_service",
        ExportService,
        protocol=ExportServiceProtocol,
    )
