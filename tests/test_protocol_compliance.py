from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Protocol, assert_type, runtime_checkable

import pandas as pd
import pytest

from yosai_intel_dashboard.src.core.protocols import (
    AnalyticsServiceProtocol,
    ConfigurationProtocol,
    DatabaseProtocol,
    EventBusProtocol,
    SecurityServiceProtocol,
    StorageProtocol,
)
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from yosai_intel_dashboard.src.services.analytics.analytics_service import AnalyticsService


@runtime_checkable
class DataProcessorProtocol(Protocol):
    def process_access_events(self, events: pd.DataFrame) -> pd.DataFrame: ...

    def clean_data(
        self, data: pd.DataFrame, rules: Dict[str, Any] | None = None
    ) -> pd.DataFrame: ...

    def aggregate_data(
        self, data: pd.DataFrame, groupby: List[str], metrics: List[str]
    ) -> pd.DataFrame: ...

    def validate_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]: ...

    def enrich_data(
        self, data: pd.DataFrame, enrichment_sources: List[str]
    ) -> pd.DataFrame: ...


@runtime_checkable
class ConfigurationProtocolStub(Protocol):
    def get_database_config(self) -> Dict[str, Any]: ...
    def get_app_config(self) -> Dict[str, Any]: ...
    def get_security_config(self) -> Dict[str, Any]: ...
    def get_upload_config(self) -> Dict[str, Any]: ...
    def reload_config(self) -> None: ...
    def validate_config(self) -> Dict[str, Any]: ...


class DummyConfig(ConfigurationProtocolStub):
    def get_database_config(self) -> Dict[str, Any]:
        return {}

    def get_app_config(self) -> Dict[str, Any]:
        return {}

    def get_security_config(self) -> Dict[str, Any]:
        return {}

    def get_upload_config(self) -> Dict[str, Any]:
        return {}

    def reload_config(self) -> None:
        pass

    def validate_config(self) -> Dict[str, Any]:
        return {"valid": True}


class DummyDatabase(DatabaseProtocol):
    def execute_query(self, query: str, params: tuple | None = None) -> pd.DataFrame:
        return pd.DataFrame()

    def execute_command(self, command: str, params: tuple | None = None) -> None:
        pass

    def execute_batch(self, command: str, params_seq: Iterable[tuple]) -> None:
        pass

    def begin_transaction(self) -> Any:
        return object()

    def commit_transaction(self, transaction: Any) -> None:
        pass

    def rollback_transaction(self, transaction: Any) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def get_connection_info(self) -> Dict[str, Any]:
        return {}


class DummyProcessor(DataProcessorProtocol):
    def process_access_events(self, events: pd.DataFrame) -> pd.DataFrame:
        return events

    def clean_data(
        self, data: pd.DataFrame, rules: Dict[str, Any] | None = None
    ) -> pd.DataFrame:
        return data

    def aggregate_data(
        self, data: pd.DataFrame, groupby: List[str], metrics: List[str]
    ) -> pd.DataFrame:
        return data

    def validate_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        return {}

    def enrich_data(
        self, data: pd.DataFrame, enrichment_sources: List[str]
    ) -> pd.DataFrame:
        return data


class DummyEventBus(EventBusProtocol):
    def publish(
        self, event_type: str, data: Dict[str, Any], source: str | None = None
    ) -> None:
        pass

    def subscribe(self, event_type: str, handler: Callable, priority: int = 0) -> str:
        return "id"

    def unsubscribe(self, subscription_id: str) -> None:
        pass

    def get_subscribers(self, event_type: str | None = None) -> List[Dict[str, Any]]:
        return []

    def get_event_history(
        self, event_type: str | None = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        return []


class DummyStorage(StorageProtocol):
    def store_data(self, key: str, data: Any) -> str:
        return key

    def retrieve_data(self, key: str) -> Any:
        return None

    def delete_data(self, key: str) -> bool:
        return True

    def list_keys(self, prefix: str = "") -> List[str]:
        return []

    def exists(self, key: str) -> bool:
        return False

    def get_storage_info(self) -> Dict[str, Any]:
        return {}


@pytest.fixture(autouse=True)
def env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in [
        "SECRET_KEY",
        "DB_PASSWORD",
        "AUTH0_CLIENT_ID",
        "AUTH0_CLIENT_SECRET",
        "AUTH0_DOMAIN",
        "AUTH0_AUDIENCE",
    ]:
        monkeypatch.setenv(var, "test")


class TestProtocolCompliance:
    def test_configuration_service_compliance(self):
        from config import create_config_manager

        cfg = create_config_manager()
        assert isinstance(cfg, ConfigurationProtocol)
        assert_type(cfg, ConfigurationProtocol)

    def test_analytics_service_compliance(self):
        from yosai_intel_dashboard.src.services.analytics.analytics_service import AnalyticsService

        class ConcreteAnalyticsService(AnalyticsService):
            def analyze_access_patterns(self, days: int) -> Dict[str, Any]:
                return {}

            def detect_anomalies(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
                return []

            def generate_report(
                self, report_type: str, params: Dict[str, Any]
            ) -> Dict[str, Any]:
                return {}

        service = ConcreteAnalyticsService(
            database=DummyDatabase(),
            data_processor=DummyProcessor(),
            config=DummyConfig(),
            event_bus=DummyEventBus(),
            storage=DummyStorage(),
        )
        assert isinstance(service, AnalyticsServiceProtocol)
        assert_type(service, AnalyticsServiceProtocol)

    def test_security_service_compliance(self):
        from validation.security_validator import SecurityValidator

        service = SecurityValidator()
        assert isinstance(service, SecurityServiceProtocol)
        assert_type(service, SecurityServiceProtocol)

    def test_all_registered_services_implement_protocols(self):
        from startup.service_registration import register_all_services

        container = ServiceContainer()
        register_all_services(container)

        # Override heavy service implementations with lightweight dummies
        container.register_singleton(
            "database_manager",
            DummyDatabase,
            protocol=DatabaseProtocol,
            factory=lambda c: DummyDatabase(),
        )
        container.register_singleton(
            "data_processor",
            DummyProcessor,
            protocol=DataProcessorProtocol,
            factory=lambda c: DummyProcessor(),
        )
        container.register_singleton(
            "event_bus",
            DummyEventBus,
            protocol=EventBusProtocol,
            factory=lambda c: DummyEventBus(),
        )
        container.register_singleton(
            "file_storage",
            DummyStorage,
            protocol=StorageProtocol,
            factory=lambda c: DummyStorage(),
        )

        assert isinstance(
            container.get("config_manager", ConfigurationProtocol),
            ConfigurationProtocol,
        )
        assert isinstance(
            container.get("security_validator", SecurityServiceProtocol),
            SecurityServiceProtocol,
        )
        from yosai_intel_dashboard.src.services.analytics.protocols import (
            DataLoadingProtocol,
            DataProcessorProtocol,
            PublishingProtocol,
            ReportGeneratorProtocol,
        )

        assert isinstance(
            container.get("data_loader", DataLoadingProtocol),
            DataLoadingProtocol,
        )
        assert isinstance(
            container.get("data_processing_service", DataProcessorProtocol),
            DataProcessorProtocol,
        )
        assert isinstance(
            container.get("report_generator", ReportGeneratorProtocol),
            ReportGeneratorProtocol,
        )
        assert isinstance(
            container.get("publisher", PublishingProtocol),
            PublishingProtocol,
        )
